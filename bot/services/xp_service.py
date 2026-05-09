"""XP and leveling system."""
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import crud
from bot.database.models import User, AchievementType


# Level N requires level * (level + 1) * 50 total XP
# Level 1→2: 100 XP | 2→3: 300 | 3→4: 600 | 4→5: 1000 | 5→6: 1500

def calculate_level(xp: int) -> int:
    level = 1
    while xp >= level * (level + 1) * 50:
        level += 1
    return level


def xp_for_level(level: int) -> int:
    """Minimum XP required to be at this level."""
    if level <= 1:
        return 0
    return (level - 1) * level * 50


def xp_for_next_level(level: int) -> int:
    """XP threshold to reach the next level."""
    return level * (level + 1) * 50


def xp_progress(xp: int, level: int) -> tuple[int, int]:
    """Returns (current_progress, needed_for_next_level)."""
    current_floor = xp_for_level(level)
    next_threshold = xp_for_next_level(level)
    return xp - current_floor, next_threshold - current_floor


ACHIEVEMENT_CHECKS = {
    AchievementType.LEVEL_5: lambda u: u.level >= 5,
    AchievementType.LEVEL_10: lambda u: u.level >= 10,
    AchievementType.LEVEL_25: lambda u: u.level >= 25,
}

DAILY_STREAK_XP = {
    1: 50, 2: 50, 3: 75, 4: 75, 5: 100, 6: 100,
}
DEFAULT_DAILY_XP = 150


class XPService:
    async def award_xp(
        self,
        session: AsyncSession,
        user: User,
        amount: int,
        multiplier: float = 1.0,
    ) -> tuple[int, bool, List[AchievementType]]:
        """
        Award XP to a user. Returns (actual_xp_awarded, leveled_up, new_achievements).
        """
        actual = max(1, int(amount * multiplier))
        old_level = user.level
        user = await crud.update_user_xp(session, user.id, actual)

        new_level = calculate_level(user.xp_points)
        leveled_up = new_level > old_level
        if leveled_up:
            user.level = new_level

        # Check achievements
        new_achievements: List[AchievementType] = []
        for ach_type, check in ACHIEVEMENT_CHECKS.items():
            if check(user):
                ach = await crud.grant_achievement(session, user.id, ach_type)
                if ach:
                    new_achievements.append(ach_type)

        return actual, leveled_up, new_achievements

    async def process_daily_checkin(
        self, session: AsyncSession, user: User
    ) -> Optional[tuple[int, int]]:
        """
        Process daily check-in. Returns (xp_awarded, streak) or None if already done today.
        """
        now = datetime.now(timezone.utc)
        today = now.date()

        if user.last_checkin_date:
            last_date = user.last_checkin_date.date()
            if last_date == today:
                return None
            if last_date == today - timedelta(days=1):
                new_streak = user.daily_streak + 1
            else:
                new_streak = 1
        else:
            new_streak = 1

        xp = DAILY_STREAK_XP.get(new_streak, DEFAULT_DAILY_XP)

        user.daily_streak = new_streak
        user.last_checkin_date = now

        await crud.create_checkin(session, user.id, new_streak, xp)

        # Streak achievements
        if new_streak >= 7:
            await crud.grant_achievement(session, user.id, AchievementType.DAILY_STREAK_7)
        if new_streak >= 30:
            await crud.grant_achievement(session, user.id, AchievementType.DAILY_STREAK_30)

        return xp, new_streak


xp_service = XPService()
