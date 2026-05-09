from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import crud
from bot.database.models import User, UserRole, TaskStatus
from bot.keyboards.inline import moderation_submission_keyboard, moderation_reject_reasons_keyboard
from bot.keyboards.reply import main_menu
from bot.utils.helpers import h

router = Router(name="moderation")

REJECT_REASONS = {
    "proof": "Недостаточно доказательств выполнения задания",
    "format": "Неверный формат доказательства",
    "incomplete": "Задание не выполнено должным образом",
    "rules": "Нарушение правил платформы",
}


class ModerationFSM(StatesGroup):
    waiting_reject_reason = State()


def _is_moderator(user: User) -> bool:
    return user.role in (UserRole.MODERATOR, UserRole.DEVELOPER)


@router.message(Command("moderation"))
@router.message(F.text == "🛡 Модерация")
async def cmd_moderation(message: Message, session: AsyncSession, user: User) -> None:
    if not _is_moderator(user):
        await message.answer("⛔ Недостаточно прав.")
        return
    pending_count = await crud.get_pending_submissions_count(session)
    await message.answer(
        f"🛡 <b>Панель модерации</b>\n\n"
        f"⏳ Заявок на проверке: <b>{pending_count}</b>\n\n"
        f"Нажмите /mod_next чтобы начать проверку"
    )


@router.message(Command("mod_next"))
@router.callback_query(F.data == "mod:next")
async def show_next_submission(event, session: AsyncSession, user: User, bot: Bot) -> None:
    is_cb = isinstance(event, CallbackQuery)
    if not _is_moderator(user):
        if is_cb:
            await event.answer("⛔ Недостаточно прав.", show_alert=True)
        else:
            await event.answer("⛔ Недостаточно прав.")
        return

    submissions = await crud.get_pending_submissions(session, limit=1)
    if not submissions:
        text = "✅ Очередь модерации пуста! Все заявки проверены."
        if is_cb:
            await event.message.edit_text(text)
            await event.answer()
        else:
            await event.answer(text)
        return

    sub = submissions[0]
    task = sub.task
    submitter = sub.user

    text = (
        f"🔍 <b>Заявка #{sub.id}</b>\n\n"
        f"👤 Пользователь: {h(submitter.display_name)}\n"
        f"🎯 Задание: <b>{h(task.title)}</b>\n"
        f"📅 Отправлено: {sub.submitted_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"✨ Награда: +{task.xp_reward} XP\n"
    )
    if sub.proof_text:
        text += f"\n📝 <b>Текст:</b>\n{h(sub.proof_text[:500])}"
    if sub.proof_link:
        text += f"\n🔗 <b>Ссылка:</b> {h(sub.proof_link)}"

    keyboard = moderation_submission_keyboard(sub.id)
    chat_id = event.message.chat.id if is_cb else event.chat.id

    if is_cb:
        await event.message.edit_text(text, reply_markup=keyboard)
        await event.answer()
    else:
        await event.answer(text, reply_markup=keyboard)

    if sub.proof_photo_file_id:
        await bot.send_photo(chat_id, sub.proof_photo_file_id, caption="📷 Доказательство")
    if sub.proof_video_file_id:
        await bot.send_video(chat_id, sub.proof_video_file_id, caption="🎥 Доказательство")


@router.callback_query(F.data.startswith("mod:approve:"))
async def cb_approve(cb: CallbackQuery, session: AsyncSession, user: User, bot: Bot) -> None:
    if not _is_moderator(user):
        await cb.answer("⛔ Недостаточно прав.", show_alert=True)
        return

    sub_id = int(cb.data.split(":")[2])
    sub = await crud.get_submission_by_id(session, sub_id)
    if not sub or sub.status != TaskStatus.PENDING:
        await cb.answer("Заявка уже обработана.", show_alert=True)
        return

    from bot.services.task_service import task_service
    result = await task_service.approve_submission(session, sub_id, user.id)
    if not result:
        await cb.answer("Ошибка при одобрении.", show_alert=True)
        return

    submitter = await crud.get_user_by_id(session, sub.user_id)
    task = sub.task
    try:
        await bot.send_message(
            submitter.telegram_id,
            f"✅ <b>Ваша заявка одобрена!</b>\n\n"
            f"🎯 Задание: <b>{h(task.title)}</b>\n"
            f"✨ Начислено: <b>+{sub.xp_awarded} XP</b>",
        )
    except Exception:
        pass

    await cb.message.edit_text(
        f"✅ Заявка #{sub_id} одобрена. +{sub.xp_awarded} XP начислено пользователю."
    )
    await cb.answer("✅ Одобрено!")


@router.callback_query(F.data.startswith("mod:reject:") & ~F.data.startswith("mod:reject_"))
async def cb_reject_menu(cb: CallbackQuery, user: User) -> None:
    if not _is_moderator(user):
        await cb.answer("⛔ Недостаточно прав.", show_alert=True)
        return
    sub_id = int(cb.data.split(":")[2])
    await cb.message.edit_reply_markup(reply_markup=moderation_reject_reasons_keyboard(sub_id))
    await cb.answer()


@router.callback_query(F.data.startswith("mod:reject_reason:"))
async def cb_reject_reason(cb: CallbackQuery, session: AsyncSession, user: User, bot: Bot) -> None:
    if not _is_moderator(user):
        await cb.answer("⛔ Недостаточно прав.", show_alert=True)
        return
    parts = cb.data.split(":")
    sub_id = int(parts[2])
    reason_code = parts[3]
    reason = REJECT_REASONS.get(reason_code, "Нарушение правил")
    await _do_reject(cb, session, user, bot, sub_id, reason)


@router.callback_query(F.data.startswith("mod:reject_custom:"))
async def cb_reject_custom(cb: CallbackQuery, state: FSMContext, user: User) -> None:
    if not _is_moderator(user):
        await cb.answer("⛔ Недостаточно прав.", show_alert=True)
        return
    sub_id = int(cb.data.split(":")[2])
    await state.set_state(ModerationFSM.waiting_reject_reason)
    await state.update_data(sub_id=sub_id)
    await cb.message.answer("✏️ Введите причину отклонения:")
    await cb.answer()


@router.message(ModerationFSM.waiting_reject_reason)
async def handle_reject_reason(message: Message, session: AsyncSession, user: User, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    sub_id = data["sub_id"]
    await state.clear()

    sub = await crud.get_submission_by_id(session, sub_id)
    if not sub or sub.status != TaskStatus.PENDING:
        await message.answer("Заявка уже обработана.")
        return

    from bot.services.task_service import task_service
    await task_service.reject_submission(session, sub_id, user.id, comment=message.text)

    submitter = await crud.get_user_by_id(session, sub.user_id)
    task = sub.task
    try:
        await bot.send_message(
            submitter.telegram_id,
            f"❌ <b>Ваша заявка отклонена</b>\n\n"
            f"🎯 Задание: <b>{h(task.title)}</b>\n"
            f"💬 Причина: {h(message.text)}",
        )
    except Exception:
        pass

    await message.answer(f"❌ Заявка #{sub_id} отклонена.\n💬 Причина: {h(message.text)}")


async def _do_reject(cb, session, user, bot, sub_id, reason):
    from bot.services.task_service import task_service
    sub = await crud.get_submission_by_id(session, sub_id)
    if not sub or sub.status != TaskStatus.PENDING:
        await cb.answer("Заявка уже обработана.", show_alert=True)
        return

    await task_service.reject_submission(session, sub_id, user.id, comment=reason)

    submitter = await crud.get_user_by_id(session, sub.user_id)
    task = sub.task
    try:
        await bot.send_message(
            submitter.telegram_id,
            f"❌ <b>Ваша заявка отклонена</b>\n\n"
            f"🎯 Задание: <b>{h(task.title)}</b>\n"
            f"💬 Причина: {h(reason)}",
        )
    except Exception:
        pass

    await cb.message.edit_text(f"❌ Заявка #{sub_id} отклонена.\n💬 Причина: {h(reason)}")
    await cb.answer("❌ Отклонено.")
