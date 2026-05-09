from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database import crud
from bot.database.models import User
from bot.keyboards.reply import main_menu
from bot.services.referral_service import referral_service
from bot.utils.helpers import h

router = Router(name="start")


def _mini_app_markup():
    """Inline keyboard with Mini App button (if URL configured)."""
    url = settings.MINI_APP_URL
    if not url:
        return None
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="🚀 Открыть Tasker App",
            web_app=WebAppInfo(url=url),
        )
    )
    return builder.as_markup()


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession, user: User) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) > 1 and args[1].startswith("ref_"):
        ref_code = args[1][4:]
        referrer = await crud.get_user_by_referral_code(session, ref_code)
        if referrer and referrer.id != user.id and not user.referred_by_id:
            await referral_service.process_referral(session, referrer.telegram_id, user.id)
            await message.answer(
                f"🎁 Вы зарегистрировались по ссылке пользователя "
                f"<b>{h(referrer.display_name)}</b> и получили <b>+50 XP</b>!"
            )

    inline_kb = _mini_app_markup()

    await message.answer(
        f"👋 Добро пожаловать в <b>TON Tasks Bot</b>, {h(user.first_name)}!\n\n"
        f"🎯 Выполняйте задания и зарабатывайте <b>XP</b>\n"
        f"🏆 Поднимайтесь в таблице лидеров\n"
        f"💰 Подключите <b>TON-кошелёк</b> и получите +500 XP\n"
        f"👥 Приглашайте друзей через реферальную программу\n\n"
        + (f"📱 Или откройте полноценное <b>Mini App</b> 👇" if settings.MINI_APP_URL else "Выберите действие в меню ниже 👇"),
        reply_markup=main_menu(user.role.value),
    )

    if inline_kb:
        await message.answer(
            "Нажмите кнопку чтобы открыть Tasker Mini App:",
            reply_markup=inline_kb,
        )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "<b>Команды бота:</b>\n\n"
        "/start — главное меню\n"
        "/profile — ваш профиль\n"
        "/tasks — список заданий\n"
        "/wallet — управление кошельком\n"
        "/leaderboard — таблица лидеров\n"
        "/referral — реферальная программа\n"
        "/checkin — ежедневный бонус\n"
        "/help — помощь"
    )
