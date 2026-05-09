from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from ..deps import CurrentUserDep, SessionDep
from ..schemas import ModerationSubmission, MessageResponse, ReviewRequest
from bot.database.models import Task, TaskSubmission, TaskStatus, User, UserRole

router = APIRouter(prefix="/moderation", tags=["moderation"])


def _require_moderator(current: dict):
    # role check is done at query time against DB; basic guard here
    pass


@router.get("/pending", response_model=list[ModerationSubmission])
async def get_pending(
    session: SessionDep,
    current: CurrentUserDep,
    limit: int = 20,
    offset: int = 0,
):
    # Verify moderator role
    u_res = await session.execute(select(User).where(User.id == current["user_id"]))
    mod_user = u_res.scalar_one_or_none()
    if not mod_user or mod_user.role not in (UserRole.MODERATOR, UserRole.DEVELOPER):
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await session.execute(
        select(TaskSubmission)
        .where(TaskSubmission.status == TaskStatus.PENDING)
        .order_by(TaskSubmission.submitted_at)
        .offset(offset)
        .limit(limit)
    )
    subs = result.scalars().all()

    out = []
    for s in subs:
        proof_file_url = None
        if s.proof_photo_file_id and s.proof_photo_file_id.startswith("uploads/"):
            proof_file_url = f"/static/{s.proof_photo_file_id}"
        elif s.proof_video_file_id and s.proof_video_file_id.startswith("uploads/"):
            proof_file_url = f"/static/{s.proof_video_file_id}"

        user_name = s.user.display_name if s.user else f"User#{s.user_id}"
        task_title = s.task.title if s.task else f"Task#{s.task_id}"
        out.append(
            ModerationSubmission(
                id=s.id,
                user_id=s.user_id,
                user_display_name=user_name,
                task_id=s.task_id,
                task_title=task_title,
                status=s.status.value,
                submitted_at=s.submitted_at,
                proof_link=s.proof_link,
                proof_text=s.proof_text,
                proof_file_url=proof_file_url,
            )
        )
    return out


@router.post("/{submission_id}/approve", response_model=MessageResponse)
async def approve_submission(
    session: SessionDep,
    current: CurrentUserDep,
    submission_id: int,
    body: ReviewRequest,
):
    from datetime import datetime, timezone

    u_res = await session.execute(select(User).where(User.id == current["user_id"]))
    mod_user = u_res.scalar_one_or_none()
    if not mod_user or mod_user.role not in (UserRole.MODERATOR, UserRole.DEVELOPER):
        raise HTTPException(status_code=403, detail="Not authorized")

    sub_res = await session.execute(
        select(TaskSubmission).where(TaskSubmission.id == submission_id)
    )
    sub = sub_res.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    if sub.status != TaskStatus.PENDING:
        raise HTTPException(status_code=409, detail="Submission already reviewed")

    task_res = await session.execute(select(Task).where(Task.id == sub.task_id))
    task = task_res.scalar_one()
    xp = task.xp_reward

    sub.status = TaskStatus.APPROVED
    sub.reviewer_id = current["user_id"]
    sub.review_comment = body.comment
    sub.xp_awarded = xp
    sub.reviewed_at = datetime.now(timezone.utc)

    # Award XP to user
    user_res = await session.execute(select(User).where(User.id == sub.user_id))
    user = user_res.scalar_one()
    user.xp_points += xp
    task.completions_count += 1

    await session.commit()
    return MessageResponse(message=f"Approved. +{xp} XP awarded to user.", xp_awarded=xp)


@router.post("/{submission_id}/reject", response_model=MessageResponse)
async def reject_submission(
    session: SessionDep,
    current: CurrentUserDep,
    submission_id: int,
    body: ReviewRequest,
):
    from datetime import datetime, timezone

    u_res = await session.execute(select(User).where(User.id == current["user_id"]))
    mod_user = u_res.scalar_one_or_none()
    if not mod_user or mod_user.role not in (UserRole.MODERATOR, UserRole.DEVELOPER):
        raise HTTPException(status_code=403, detail="Not authorized")

    sub_res = await session.execute(
        select(TaskSubmission).where(TaskSubmission.id == submission_id)
    )
    sub = sub_res.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    if sub.status != TaskStatus.PENDING:
        raise HTTPException(status_code=409, detail="Submission already reviewed")

    sub.status = TaskStatus.REJECTED
    sub.reviewer_id = current["user_id"]
    sub.review_comment = body.comment
    sub.reviewed_at = datetime.now(timezone.utc)

    await session.commit()
    return MessageResponse(message="Submission rejected.")
