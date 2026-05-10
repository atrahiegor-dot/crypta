from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter
from sqlalchemy import and_, desc, func, select

from ..deps import CurrentUserDep, SessionDep
from ..schemas import LeaderboardEntry
from bot.database.models import TaskSubmission, TaskStatus, User

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


@router.get("", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    session: SessionDep,
    current: CurrentUserDep,
    period: str = "all",  # all | weekly | monthly
    limit: int = 50,
    offset: int = 0,
):
    current_uid = current["user_id"]

    if period == "all":
        result = await session.execute(
            select(User)
            .where(User.is_banned == False)
            .order_by(desc(User.xp_points))
            .offset(offset)
            .limit(limit)
        )
        users = result.scalars().all()
        entries = []
        for i, u in enumerate(users):
            entries.append(
                LeaderboardEntry(
                    rank=offset + i + 1,
                    user_id=u.id,
                    username=u.username,
                    first_name=u.first_name,
                    display_name=u.display_name,
                    xp_points=u.xp_points,
                    level=u.level,
                    is_current_user=(u.id == current_uid),
                )
            )
        return entries

    # Period-based leaderboard
    now = datetime.now(timezone.utc)
    if period == "weekly":
        since = now - timedelta(days=7)
    else:
        since = now - timedelta(days=30)

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

    return [
        LeaderboardEntry(
            rank=offset + i + 1,
            user_id=row[0].id,
            username=row[0].username,
            first_name=row[0].first_name,
            display_name=row[0].display_name,
            xp_points=int(row[1] or 0),
            level=row[0].level,
            is_current_user=(row[0].id == current_uid),
        )
        for i, row in enumerate(rows)
    ]
