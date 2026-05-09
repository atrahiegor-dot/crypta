from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import User
from bot.services.xp_service import xp_service
from bot.utils.helpers import h, ACHIEVEMENT_INFO

router = Router(name="checkin")


@router.message(Command("checkin"))
@router.message(F.text == "📅 Ежедневный бонус")
async def cmd_checkin(message: Message, session: AsyncSession, user: User) -> None:
    result = await xp_service.process_daily_checkin(session, user)

    if result is None:
        await message.answer(
            f"⏰ Вы уже получили бонус сегодня!\n\n"
            f"🔥 Текущая серия: <b>{user.daily_streak}</b> дней\n"
            f"📅 Следующий бонус будет доступен завтра"
        )
        return

    xp, streak = result
    _, leveled_up, new_achievements = await xp_service.award_xp(session, user, xp)

    streak_bar = "🔥" * min(streak, 7)
    text = (
        f"🎁 <b>Ежедневный бонус получен!</b>\n\n"
        f"✨ Начислено: <b>+{xp} XP</b>\n"
        f"🔥 Серия: <b>{streak}</b> дней {streak_bar}"
    )
    if leveled_up:
        text += f"\n\n🎉 <b>Поздравляем! Уровень повышен до {user.level}!</b>"
    if new_achievements:
        for ach_type in new_achievements:
            info = ACHIEVEMENT_INFO.get(ach_type)
            if info:
                emoji, name, _ = info
                text += f"\n🏅 Достижение: <b>{emoji} {h(name)}</b>"

    await message.answer(text)
