from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple

from sqlalchemy import select, update, func, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import (
    User, Task, TaskSubmission, Referral, Achievement, DailyCheckIn,
    BonusEvent, UserRole, TaskStatus, TaskCategory, AchievementType,
)


# ─── Users ────────────────────────────────────────────────────────────────────

async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> Optional[User]:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_referral_code(session: AsyncSession, code: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.referral_code == code))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    telegram_id: int,
    first_name: str,
    username: Optional[str] = None,
    last_name: Optional[str] = None,
    referred_by_id: Optional[int] = None,
    role: UserRole = UserRole.USER,
) -> User:
    user = User(
        telegram_id=telegram_id,
        first_name=first_name,
        username=username,
        last_name=last_name,
        referred_by_id=referred_by_id,
        role=role,
    )
    session.add(user)
    await session.flush()
    return user


async def update_user_activity(session: AsyncSession, telegram_id: int, **fields) -> None:
    await session.execute(
        update(User)
        .where(User.telegram_id == telegram_id)
        .values(last_activity=datetime.now(timezone.utc), **fields)
    )


async def update_user_xp(session: AsyncSession, user_id: int, xp_delta: int) -> User:
    user = await get_user_by_id(session, user_id)
    user.xp_points = max(0, user.xp_points + xp_delta)
    return user


async def set_user_wallet(session: AsyncSession, user_id: int, wallet_address: str) -> User:
    user = await get_user_by_id(session, user_id)
    user.wallet_address = wallet_address
    user.wallet_connected_at = datetime.now(timezone.utc)
    return user


async def set_user_role(session: AsyncSession, user_id: int, role: UserRole) -> User:
    user = await get_user_by_id(session, user_id)
    user.role = role
    return user


async def ban_user(session: AsyncSession, user_id: int, reason: str) -> User:
    user = await get_user_by_id(session, user_id)
    user.is_banned = True
    user.ban_reason = reason
    return user


async def unban_user(session: AsyncSession, user_id: int) -> User:
    user = await get_user_by_id(session, user_id)
    user.is_banned = False
    user.ban_reason = None
    return user


async def get_total_users_count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count(User.id)))
    return result.scalar_one()


async def search_users(session: AsyncSession, query: str, limit: int = 20) -> List[User]:
    result = await session.execute(
        select(User)
        .where(
            or_(
                User.username.ilike(f"%{query}%"),
                User.first_name.ilike(f"%{query}%"),
                func.cast(User.telegram_id, str).contains(query),
            )
        )
        .limit(limit)
    )
    return list(result.scalars().all())


# ─── Leaderboard ──────────────────────────────────────────────────────────────

async def get_leaderboard(
    session: AsyncSession,
    limit: int = 100,
    offset: int = 0,
    since: Optional[datetime] = None,
) -> List[Tuple[int, User]]:
    """Returns list of (rank, user) tuples."""
    if since:
        # XP earned since a date requires summing approved submissions in that period
        subq = (
            select(
                TaskSubmission.user_id,
                func.sum(TaskSubmission.xp_awarded).label("period_xp"),
            )
            .where(
                and_(
                    TaskSubmission.status == TaskStatus.APPROVED,
                    TaskSubmission.reviewed_at >= since,
                )
            )
            .group_by(TaskSubmission.user_id)
            .subquery()
        )
        result = await session.execute(
            select(User, subq.c.period_xp)
            .join(subq, User.id == subq.c.user_id)
            .where(User.is_banned == False)
            .order_by(desc(subq.c.period_xp))
            .offset(offset)
            .limit(limit)
        )
        rows = result.all()
        return [(offset + i + 1, row[0]) for i, row in enumerate(rows)]
    else:
        result = await session.execute(
            select(User)
            .where(User.is_banned == False)
            .order_by(desc(User.xp_points))
            .offset(offset)
            .limit(limit)
        )
        users = list(result.scalars().all())
        return [(offset + i + 1, u) for i, u in enumerate(users)]


async def get_user_rank(session: AsyncSession, user_id: int) -> int:
    user = await get_user_by_id(session, user_id)
    result = await session.execute(
        select(func.count(User.id)).where(
            and_(User.xp_points > user.xp_points, User.is_banned == False)
        )
    )
    return result.scalar_one() + 1


# ─── Tasks ────────────────────────────────────────────────────────────────────

async def get_tasks(
    session: AsyncSession,
    category: Optional[TaskCategory] = None,
    is_active: bool = True,
    limit: int = 20,
    offset: int = 0,
) -> List[Task]:
    q = select(Task).where(Task.is_active == is_active)
    if category:
        q = q.where(Task.category == category)
    now = datetime.now(timezone.utc)
    q = q.where(
        or_(Task.available_from == None, Task.available_from <= now)
    ).where(
        or_(Task.available_until == None, Task.available_until >= now)
    )
    q = q.order_by(Task.id).offset(offset).limit(limit)
    result = await session.execute(q)
    return list(result.scalars().all())


async def get_task_by_id(session: AsyncSession, task_id: int) -> Optional[Task]:
    result = await session.execute(select(Task).where(Task.id == task_id))
    return result.scalar_one_or_none()


async def create_task(session: AsyncSession, **kwargs) -> Task:
    task = Task(**kwargs)
    session.add(task)
    await session.flush()
    return task


async def update_task(session: AsyncSession, task_id: int, **kwargs) -> Optional[Task]:
    task = await get_task_by_id(session, task_id)
    if not task:
        return None
    for key, value in kwargs.items():
        setattr(task, key, value)
    return task


async def delete_task(session: AsyncSession, task_id: int) -> bool:
    task = await get_task_by_id(session, task_id)
    if not task:
        return False
    task.is_active = False
    return True


async def get_tasks_count(session: AsyncSession) -> int:
    result = await session.execute(select(func.count(Task.id)).where(Task.is_active == True))
    return result.scalar_one()


# ─── Submissions ──────────────────────────────────────────────────────────────

async def create_submission(
    session: AsyncSession,
    user_id: int,
    task_id: int,
    proof_text: Optional[str] = None,
    proof_photo_file_id: Optional[str] = None,
    proof_video_file_id: Optional[str] = None,
    proof_link: Optional[str] = None,
) -> TaskSubmission:
    sub = TaskSubmission(
        user_id=user_id,
        task_id=task_id,
        proof_text=proof_text,
        proof_photo_file_id=proof_photo_file_id,
        proof_video_file_id=proof_video_file_id,
        proof_link=proof_link,
    )
    session.add(sub)
    await session.flush()
    return sub


async def get_submission_by_id(session: AsyncSession, sub_id: int) -> Optional[TaskSubmission]:
    result = await session.execute(select(TaskSubmission).where(TaskSubmission.id == sub_id))
    return result.scalar_one_or_none()


async def get_pending_submissions(
    session: AsyncSession, limit: int = 20, offset: int = 0
) -> List[TaskSubmission]:
    result = await session.execute(
        select(TaskSubmission)
        .where(TaskSubmission.status == TaskStatus.PENDING)
        .order_by(TaskSubmission.submitted_at)
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_pending_submissions_count(session: AsyncSession) -> int:
    result = await session.execute(
        select(func.count(TaskSubmission.id)).where(TaskSubmission.status == TaskStatus.PENDING)
    )
    return result.scalar_one()


async def review_submission(
    session: AsyncSession,
    submission_id: int,
    reviewer_id: int,
    status: TaskStatus,
    comment: Optional[str] = None,
    xp_awarded: int = 0,
) -> TaskSubmission:
    sub = await get_submission_by_id(session, submission_id)
    sub.status = status
    sub.reviewer_id = reviewer_id
    sub.review_comment = comment
    sub.xp_awarded = xp_awarded
    sub.reviewed_at = datetime.now(timezone.utc)
    return sub


async def has_user_completed_task(session: AsyncSession, user_id: int, task_id: int) -> bool:
    result = await session.execute(
        select(TaskSubmission).where(
            and_(
                TaskSubmission.user_id == user_id,
                TaskSubmission.task_id == task_id,
                TaskSubmission.status == TaskStatus.APPROVED,
            )
        )
    )
    return result.scalar_one_or_none() is not None


async def has_user_pending_submission(session: AsyncSession, user_id: int, task_id: int) -> bool:
    result = await session.execute(
        select(TaskSubmission).where(
            and_(
                TaskSubmission.user_id == user_id,
                TaskSubmission.task_id == task_id,
                TaskSubmission.status == TaskStatus.PENDING,
            )
        )
    )
    return result.scalar_one_or_none() is not None


async def get_user_submissions(
    session: AsyncSession, user_id: int, limit: int = 10, offset: int = 0
) -> List[TaskSubmission]:
    result = await session.execute(
        select(TaskSubmission)
        .where(TaskSubmission.user_id == user_id)
        .order_by(desc(TaskSubmission.submitted_at))
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


# ─── Referrals ────────────────────────────────────────────────────────────────

async def create_referral(
    session: AsyncSession,
    referrer_id: int,
    referred_id: int,
    xp_referrer: int,
    xp_referred: int,
) -> Referral:
    ref = Referral(
        referrer_id=referrer_id,
        referred_id=referred_id,
        xp_earned_referrer=xp_referrer,
        xp_earned_referred=xp_referred,
    )
    session.add(ref)
    await session.flush()
    return ref


async def get_user_referrals(
    session: AsyncSession, user_id: int, limit: int = 20, offset: int = 0
) -> List[Referral]:
    result = await session.execute(
        select(Referral)
        .where(Referral.referrer_id == user_id)
        .order_by(desc(Referral.created_at))
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_referral_count(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        select(func.count(Referral.id)).where(Referral.referrer_id == user_id)
    )
    return result.scalar_one()


# ─── Achievements ─────────────────────────────────────────────────────────────

async def grant_achievement(
    session: AsyncSession,
    user_id: int,
    achievement_type: AchievementType,
    meta: Optional[dict] = None,
) -> Optional[Achievement]:
    existing = await session.execute(
        select(Achievement).where(
            and_(
                Achievement.user_id == user_id,
                Achievement.achievement_type == achievement_type,
            )
        )
    )
    if existing.scalar_one_or_none():
        return None
    ach = Achievement(user_id=user_id, achievement_type=achievement_type, meta=meta)
    session.add(ach)
    await session.flush()
    return ach


# ─── Daily Check-In ───────────────────────────────────────────────────────────

async def create_checkin(
    session: AsyncSession, user_id: int, streak: int, xp_earned: int
) -> DailyCheckIn:
    checkin = DailyCheckIn(user_id=user_id, streak=streak, xp_earned=xp_earned)
    session.add(checkin)
    await session.flush()
    return checkin


# ─── Bonus Events ─────────────────────────────────────────────────────────────

async def get_active_bonus_event(session: AsyncSession) -> Optional[BonusEvent]:
    now = datetime.now(timezone.utc)
    result = await session.execute(
        select(BonusEvent).where(
            and_(
                BonusEvent.is_active == True,
                BonusEvent.starts_at <= now,
                BonusEvent.ends_at >= now,
            )
        ).order_by(desc(BonusEvent.xp_multiplier)).limit(1)
    )
    return result.scalar_one_or_none()


async def get_all_bonus_events(session: AsyncSession) -> List[BonusEvent]:
    result = await session.execute(
        select(BonusEvent).order_by(desc(BonusEvent.created_at))
    )
    return list(result.scalars().all())
