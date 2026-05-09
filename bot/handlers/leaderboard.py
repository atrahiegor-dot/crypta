from datetime import datetime, timezone, timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import crud
from bot.database.models import User
from bot.keyboards.inline import leaderboard_keyboard
from bot.utils.helpers import format_leaderboard

router = Router(name="leaderboard")


async def _leaderboard_text(session: AsyncSession, user: User, period: str) -> str:
    now = datetime.now(timezone.utc)
    since = None
    period_label = "🌐 Всё время"
    if period == "week":
        since = now - timedelta(days=7)
        period_label = "📅 За неделю"
    elif period == "month":
        since = now - timedelta(days=30)
        period_label = "📆 За месяц"

    entries = await crud.get_leaderboard(session, limit=10, since=since)
    rank = await crud.get_user_rank(session, user.id)
    text = f"<b>{period_label}</b>\n\n"
    text += format_leaderboard(entries, viewer_id=user.telegram_id)
    text += f"\n\n📍 Ваше место: <b>#{rank}</b> | {user.xp_points:,} XP"
    return text


@router.message(Command("leaderboard"))
@router.message(F.text == "🏆 Рейтинг")
async def cmd_leaderboard(message: Message, session: AsyncSession, user: User) -> None:
    text = await _leaderboard_text(session, user, "all")
    await message.answer(text, reply_markup=leaderboard_keyboard("all"))


@router.callback_query(F.data.startswith("lb:"))
async def cb_leaderboard(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    period = cb.data.split(":")[1]
    text = await _leaderboard_text(session, user, period)
    await cb.message.edit_text(text, reply_markup=leaderboard_keyboard(period))
    await cb.answer()
