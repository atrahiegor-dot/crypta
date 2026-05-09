from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database import crud
from bot.database.models import User, AchievementType
from bot.keyboards.inline import wallet_connect_keyboard, wallet_connected_keyboard
from bot.keyboards.reply import main_menu
from bot.services.ton_connect import ton_connect_service, generate_qr_image
from bot.services.xp_service import xp_service
from bot.utils.helpers import h, code

router = Router(name="wallet")


@router.message(Command("wallet"))
@router.message(F.text == "💰 Кошелёк")
async def cmd_wallet(message: Message, session: AsyncSession, user: User) -> None:
    if user.wallet_address:
        await message.answer(
            f"💰 <b>Ваш TON-кошелёк</b>\n\n"
            f"📍 Адрес: {code(user.wallet_address)}\n"
            f"📅 Подключён: {user.wallet_connected_at.strftime('%d.%m.%Y')}",
            reply_markup=wallet_connected_keyboard(),
        )
        return

    if not settings.TON_CONNECT_MANIFEST_URL:
        await message.answer(
            "⚠️ TON Connect не настроен. Обратитесь к администратору.\n\n"
            f"Заполните <code>TON_CONNECT_MANIFEST_URL</code> в файле <code>.env</code>"
        )
        return

    try:
        connect_url, _ = await ton_connect_service.generate_connect_url(user.telegram_id)
    except Exception as e:
        await message.answer("❌ Не удалось создать запрос подключения. Попробуйте позже.")
        return

    qr = generate_qr_image(connect_url)
    qr_file = BufferedInputFile(qr.read(), filename="qr.png")
    await message.answer_photo(
        qr_file,
        caption=(
            f"💰 <b>Подключите TON-кошелёк</b>\n\n"
            f"📱 Отсканируйте QR-код в приложении <b>Tonkeeper</b> или нажмите кнопку ниже\n\n"
            f"🎁 После подключения вы получите <b>+{settings.WALLET_CONNECT_XP} XP</b>!"
        ),
        reply_markup=wallet_connect_keyboard(connect_url),
    )


@router.callback_query(F.data == "wallet:check")
async def cb_wallet_check(cb: CallbackQuery, session: AsyncSession, user: User, bot: Bot) -> None:
    await cb.answer("⏳ Проверяем подключение...")
    fresh_user = await crud.get_user_by_id(session, user.id)
    if fresh_user.wallet_address:
        await cb.message.edit_caption(
            caption=f"✅ <b>Кошелёк уже подключён!</b>\n\n📍 {code(fresh_user.wallet_address)}",
            reply_markup=wallet_connected_keyboard(),
        )
        return

    address = await ton_connect_service.check_connection(user.telegram_id)
    if not address:
        await cb.answer("❌ Кошелёк ещё не подключён. Подтвердите в приложении.", show_alert=True)
        return

    await _save_wallet(session, fresh_user, address, bot, cb.message.chat.id)
    await cb.message.edit_caption(
        caption=(
            f"✅ <b>Кошелёк успешно подключён!</b>\n\n"
            f"📍 {code(address)}\n"
            f"🎁 Начислено <b>+{settings.WALLET_CONNECT_XP} XP</b>"
        ),
        reply_markup=wallet_connected_keyboard(),
    )
    ton_connect_service.cleanup_connector(user.telegram_id)


@router.callback_query(F.data == "wallet:cancel")
async def cb_wallet_cancel(cb: CallbackQuery, user: User) -> None:
    ton_connect_service.cleanup_connector(user.telegram_id)
    await cb.message.delete()
    await cb.answer("Отменено.")


@router.callback_query(F.data == "wallet:disconnect")
async def cb_wallet_disconnect(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    await ton_connect_service.disconnect(user.telegram_id)
    fresh_user = await crud.get_user_by_id(session, user.id)
    fresh_user.wallet_address = None
    fresh_user.wallet_connected_at = None
    await cb.message.edit_text("🔌 Кошелёк отключён.")
    await cb.answer("Кошелёк отключён.")


async def _save_wallet(session, user, address, bot, chat_id):
    await crud.set_user_wallet(session, user.id, address)
    await xp_service.award_xp(session, user, settings.WALLET_CONNECT_XP)
    ach = await crud.grant_achievement(session, user.id, AchievementType.WALLET_CONNECTED)
    if ach:
        await bot.send_message(chat_id, "🏅 Достижение разблокировано: <b>💰 TON-кошелёк</b>")
