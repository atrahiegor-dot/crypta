from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import crud
from bot.database.models import User
from bot.keyboards.inline import profile_keyboard
from bot.utils.helpers import format_profile, h, ACHIEVEMENT_INFO

router = Router(name="profile")


async def _send_profile(event, session: AsyncSession, user: User) -> None:
    rank = await crud.get_user_rank(session, user.id)
    ref_count = await crud.get_referral_count(session, user.id)
    text = format_profile(user, rank).replace("__REF__", str(ref_count))

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=profile_keyboard())
        await event.answer()
    else:
        await event.answer(text, reply_markup=profile_keyboard())


@router.message(Command("profile"))
@router.message(F.text == "👤 Профиль")
async def profile_command(message: Message, session: AsyncSession, user: User) -> None:
    await _send_profile(message, session, user)


@router.callback_query(F.data == "profile:achievements")
async def show_achievements(cb: CallbackQuery, user: User) -> None:
    if not user.achievements:
        text = "🏅 <b>Достижения</b>\n\nУ вас пока нет достижений. Выполняйте задания!"
    else:
        lines = ["🏅 <b>Ваши достижения:</b>\n"]
        for ach in user.achievements:
            info = ACHIEVEMENT_INFO.get(ach.achievement_type)
            if info:
                emoji, name, desc = info
                lines.append(f"{emoji} <b>{h(name)}</b> — {h(desc)}")
        text = "\n".join(lines)
    await cb.message.edit_text(text)
    await cb.answer()


@router.callback_query(F.data == "profile:submissions")
async def show_submissions(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    submissions = await crud.get_user_submissions(session, user.id, limit=10)
    if not submissions:
        text = "📋 <b>Мои заявки</b>\n\nЗаявок пока нет."
    else:
        STATUS_EMOJI = {"pending": "⏳", "approved": "✅", "rejected": "❌", "cancelled": "🚫"}
        lines = ["📋 <b>Последние заявки:</b>\n"]
        for sub in submissions:
            task = sub.task
            emoji = STATUS_EMOJI.get(sub.status.value, "❓")
            xp_str = f" (+{sub.xp_awarded} XP)" if sub.xp_awarded else ""
            lines.append(
                f"{emoji} {h(task.title)}{h(xp_str)}\n"
                f"   {sub.submitted_at.strftime('%d.%m.%Y %H:%M')}"
            )
        text = "\n".join(lines)
    await cb.message.edit_text(text)
    await cb.answer()


@router.message(F.text == "🏅 Достижения")
async def achievements_shortcut(message: Message, user: User) -> None:
    if not user.achievements:
        text = "🏅 <b>Достижения</b>\n\nУ вас пока нет достижений. Выполняйте задания!"
    else:
        lines = ["🏅 <b>Ваши достижения:</b>\n"]
        for ach in user.achievements:
            info = ACHIEVEMENT_INFO.get(ach.achievement_type)
            if info:
                emoji, name, desc = info
                lines.append(f"{emoji} <b>{h(name)}</b> — {h(desc)}")
        text = "\n".join(lines)
    await message.answer(text)
