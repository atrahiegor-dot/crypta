import os
import uuid
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from sqlalchemy import and_, select

from ..config import settings
from ..deps import CurrentUserDep, SessionDep
from ..schemas import MessageResponse, SubmitTaskRequest, TaskWithStatus
from bot.database.models import Task, TaskStatus, TaskSubmission, User

router = APIRouter(prefix="/tasks", tags=["tasks"])

ALLOWED_IMAGE = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_VIDEO = {"video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"}
ALLOWED_MIME = ALLOWED_IMAGE | ALLOWED_VIDEO
MAX_SIZE = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


def _task_status_for_user(
    task: Task,
    subs: list[TaskSubmission],
) -> str:
    for s in subs:
        if s.task_id == task.id:
            if s.status == TaskStatus.APPROVED:
                return "completed"
            if s.status == TaskStatus.PENDING:
                return "pending"
            if s.status == TaskStatus.REJECTED:
                return "rejected"
    return "not_started"


@router.get("", response_model=list[TaskWithStatus])
async def list_tasks(
    session: SessionDep,
    current: CurrentUserDep,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    from datetime import datetime, timezone
    from sqlalchemy import or_

    q = select(Task).where(Task.is_active == True)
    if category:
        from bot.database.models import TaskCategory
        try:
            cat = TaskCategory(category)
            q = q.where(Task.category == cat)
        except ValueError:
            pass

    now = datetime.now(timezone.utc)
    q = (
        q.where(or_(Task.available_from == None, Task.available_from <= now))
        .where(or_(Task.available_until == None, Task.available_until >= now))
        .order_by(Task.id)
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(q)
    tasks = result.scalars().all()

    # Fetch user's submissions for these task ids
    task_ids = [t.id for t in tasks]
    subs_result = await session.execute(
        select(TaskSubmission).where(
            and_(
                TaskSubmission.user_id == current["user_id"],
                TaskSubmission.task_id.in_(task_ids),
            )
        )
    )
    user_subs = list(subs_result.scalars().all())

    return [
        TaskWithStatus(
            **{c.key: getattr(t, c.key) for c in Task.__table__.columns},
            user_status=_task_status_for_user(t, user_subs),
        )
        for t in tasks
    ]


@router.get("/{task_id}", response_model=TaskWithStatus)
async def get_task(session: SessionDep, current: CurrentUserDep, task_id: int):
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task or not task.is_active:
        raise HTTPException(status_code=404, detail="Task not found")

    subs_result = await session.execute(
        select(TaskSubmission).where(
            and_(
                TaskSubmission.user_id == current["user_id"],
                TaskSubmission.task_id == task_id,
            )
        )
    )
    user_subs = list(subs_result.scalars().all())
    user_status = _task_status_for_user(task, user_subs)

    return TaskWithStatus(
        **{c.key: getattr(task, c.key) for c in Task.__table__.columns},
        user_status=user_status,
    )


@router.post("/{task_id}/submit", response_model=MessageResponse)
async def submit_task(
    session: SessionDep,
    current: CurrentUserDep,
    task_id: int,
    proof_link: Optional[str] = Form(None),
    proof_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    # Check task exists
    result = await session.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task or not task.is_active:
        raise HTTPException(status_code=404, detail="Task not found")

    user_id = current["user_id"]

    # Check already completed (non-repeatable)
    if not task.is_repeatable:
        existing = await session.execute(
            select(TaskSubmission).where(
                and_(
                    TaskSubmission.user_id == user_id,
                    TaskSubmission.task_id == task_id,
                    TaskSubmission.status == TaskStatus.APPROVED,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Task already completed")

    # Check no pending submission
    pending = await session.execute(
        select(TaskSubmission).where(
            and_(
                TaskSubmission.user_id == user_id,
                TaskSubmission.task_id == task_id,
                TaskSubmission.status == TaskStatus.PENDING,
            )
        )
    )
    if pending.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Submission already pending")

    # Validate proof requirements
    if task.requires_link and not proof_link:
        raise HTTPException(status_code=422, detail="Link proof required")
    if (task.requires_photo or task.requires_video) and not file:
        raise HTTPException(status_code=422, detail="File proof required")

    # Handle file upload
    proof_photo_file_id = None
    proof_video_file_id = None

    if file:
        content_type = file.content_type or ""
        if content_type not in ALLOWED_MIME:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type: {content_type}",
            )

        data = await file.read()
        if len(data) > MAX_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large (max {settings.MAX_UPLOAD_SIZE_MB}MB)",
            )

        ext = Path(file.filename or "file").suffix or ".bin"
        filename = f"{uuid.uuid4().hex}{ext}"
        upload_path = Path(settings.UPLOAD_DIR) / filename
        upload_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(upload_path, "wb") as f_out:
            await f_out.write(data)

        rel_path = f"uploads/{filename}"
        if content_type in ALLOWED_IMAGE:
            proof_photo_file_id = rel_path
        else:
            proof_video_file_id = rel_path

    # Create submission
    sub = TaskSubmission(
        user_id=user_id,
        task_id=task_id,
        proof_link=proof_link,
        proof_text=proof_text,
        proof_photo_file_id=proof_photo_file_id,
        proof_video_file_id=proof_video_file_id,
    )
    session.add(sub)

    # Auto-approve if no moderation needed
    if not task.requires_moderation:
        sub.status = TaskStatus.APPROVED
        sub.xp_awarded = task.xp_reward

        user_result = await session.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one()
        user.xp_points += task.xp_reward
        task.completions_count += 1

        await session.commit()
        return MessageResponse(
            message="Task completed! XP awarded.",
            xp_awarded=task.xp_reward,
        )

    await session.commit()
    return MessageResponse(
        message="Submission sent for review. You'll be notified when it's approved.",
    )
