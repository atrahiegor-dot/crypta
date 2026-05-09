"""Referral system service."""
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database import crud
from bot.database.models import AchievementType
from bot.services.xp_service import xp_service


class ReferralService:
    async def process_referral(
        self, session: AsyncSession, referrer_telegram_id: int, new_user_id: int
    ) -> bool:
        """
        Called when a new user joins with a referral link.
        Awards XP to both parties and records the referral.
        Returns True if referral was successfully processed.
        """
        referrer = await crud.get_user_by_telegram_id(session, referrer_telegram_id)
        if not referrer or referrer.is_banned:
            return False

        new_user = await crud.get_user_by_id(session, new_user_id)
        if not new_user:
            return False

        # Update referred_by field
        new_user.referred_by_id = referrer.id

        # Award XP
        xp_ref = settings.REFERRAL_XP
        await xp_service.award_xp(session, referrer, xp_ref)
        await xp_service.award_xp(session, new_user, xp_ref // 2)

        await crud.create_referral(
            session,
            referrer_id=referrer.id,
            referred_id=new_user.id,
            xp_referrer=xp_ref,
            xp_referred=xp_ref // 2,
        )

        # Referral achievements
        ref_count = await crud.get_referral_count(session, referrer.id)
        if ref_count >= 1:
            await crud.grant_achievement(session, referrer.id, AchievementType.FIRST_REFERRAL)
        if ref_count >= 10:
            await crud.grant_achievement(session, referrer.id, AchievementType.REFERRALS_10)

        return True


referral_service = ReferralService()
