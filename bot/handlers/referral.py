from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database import crud
from bot.database.models import User
from bot.utils.helpers import h, code

router = Router(name="referral")


@router.message(Command("referral"))
@router.message(F.text == "👥 Рефералы")
async def cmd_referral(message: Message, session: AsyncSession, user: User, bot: Bot) -> None:
    ref_count = await crud.get_referral_count(session, user.id)
    referrals = await crud.get_user_referrals(session, user.id, limit=5)

    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user.referral_code}"

    # Recent referrals list
    ref_lines = ""
    if referrals:
        lines = []
        for ref in referrals:
            referred = await crud.get_user_by_id(session, ref.referred_id)
            if referred:
                lines.append(f"  👤 {h(referred.display_name)} — +{ref.xp_earned_referrer} XP")
        if lines:
            ref_lines = "\n\n<b>Последние рефералы:</b>\n" + "\n".join(lines)

    text = (
        f"👥 <b>Реферальная программа</b>\n\n"
        f"👤 Приглашено пользователей: <b>{ref_count}</b>\n"
        f"✨ Бонус за реферала: <b>+{settings.REFERRAL_XP} XP</b> вам "
        f"+ <b>+{settings.REFERRAL_XP // 2} XP</b> другу"
        f"{ref_lines}\n\n"
        f"💡 Нажмите кнопку ниже чтобы скопировать вашу ссылку и поделиться ею:"
    )

    # Inline keyboard — кнопка-ссылка + кнопка "Поделиться"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🔗 Моя реферальная ссылка",
        url=ref_link,
    ))
    builder.row(InlineKeyboardButton(
        text="📤 Поделиться с другом",
        url=f"https://t.me/share/url?url={ref_link}&text=Присоединяйся+к+TON+Tasks+Bot+и+получи+бонус!",
    ))

    await message.answer(text, reply_markup=builder.as_markup())
