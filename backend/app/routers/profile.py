from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select, and_

from ..deps import CurrentUserDep, SessionDep
from ..schemas import MessageResponse, SubmissionOut, UserProfile
from bot.database.models import (
    Achievement, Referral, TaskSubmission, TaskStatus, User,
)

router = APIRouter(prefix="/profile", tags=["profile"])


async def _build_profile(session, user: User) -> UserProfile:
    # tasks completed
    res = await session.execute(
        select(func.count(TaskSubmission.id)).where(
            and_(TaskSubmission.user_id == user.id, TaskSubmission.status == TaskStatus.APPROVED)
        )
    )
    tasks_completed = res.scalar_one()

    # referrals count
    res2 = await session.execute(
        select(func.count(Referral.id)).where(Referral.referrer_id == user.id)
    )
    referrals_count = res2.scalar_one()

    # rank (users with more XP)
    res3 = await session.execute(
        select(func.count(User.id)).where(
            and_(User.xp_points > user.xp_points, User.is_banned == False)
        )
    )
    rank = res3.scalar_one() + 1

    achievements = [
        {"type": a.achievement_type.value, "earned_at": a.earned_at}
        for a in (user.achievements or [])
    ]

    return UserProfile(
        id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        display_name=user.display_name,
        xp_points=user.xp_points,
        level=user.level,
        wallet_address=user.wallet_address,
        wallet_connected=bool(user.wallet_address),
        daily_streak=user.daily_streak,
        referral_code=user.referral_code,
        role=user.role.value,
        achievements=achievements,
        tasks_completed=tasks_completed,
        referrals_count=referrals_count,
        rank=rank,
    )


@router.get("/me", response_model=UserProfile)
async def get_my_profile(session: SessionDep, current: CurrentUserDep):
    result = await session.execute(select(User).where(User.id == current["user_id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await _build_profile(session, user)


@router.get("/submissions", response_model=list[SubmissionOut])
async def get_my_submissions(
    session: SessionDep,
    current: CurrentUserDep,
    limit: int = 20,
    offset: int = 0,
):
    result = await session.execute(
        select(TaskSubmission)
        .where(TaskSubmission.user_id == current["user_id"])
        .order_by(TaskSubmission.submitted_at.desc())
        .offset(offset)
        .limit(limit)
    )
    subs = result.scalars().all()
    out = []
    for s in subs:
        task_title = s.task.title if s.task else None
        proof_file_url = None
        if s.proof_photo_file_id and s.proof_photo_file_id.startswith("uploads/"):
            proof_file_url = f"/static/{s.proof_photo_file_id}"
        elif s.proof_video_file_id and s.proof_video_file_id.startswith("uploads/"):
            proof_file_url = f"/static/{s.proof_video_file_id}"
        out.append(
            SubmissionOut(
                id=s.id,
                task_id=s.task_id,
                task_title=task_title,
                status=s.status.value,
                submitted_at=s.submitted_at,
                reviewed_at=s.reviewed_at,
                xp_awarded=s.xp_awarded,
                review_comment=s.review_comment,
                proof_link=s.proof_link,
                proof_file_url=proof_file_url,
            )
        )
    return out
