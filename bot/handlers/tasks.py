from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import crud
from bot.database.models import User, TaskCategory
from bot.keyboards.inline import (
    task_categories_keyboard, tasks_list_keyboard,
    task_detail_keyboard, CATEGORY_LABELS,
)
from bot.keyboards.reply import cancel_keyboard, main_menu
from bot.services.task_service import task_service
from bot.utils.helpers import format_task, h

router = Router(name="tasks")
PAGE_SIZE = 5


class SubmitTaskFSM(StatesGroup):
    waiting_proof_text = State()
    waiting_proof_photo = State()
    waiting_proof_video = State()
    waiting_proof_link = State()


@router.message(Command("tasks"))
@router.message(F.text == "🎯 Задания")
async def cmd_tasks(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("🎯 <b>Выберите категорию заданий:</b>", reply_markup=task_categories_keyboard())


@router.callback_query(F.data == "tasks:categories")
async def cb_categories(cb: CallbackQuery) -> None:
    await cb.message.edit_text("🎯 <b>Выберите категорию заданий:</b>", reply_markup=task_categories_keyboard())
    await cb.answer()


@router.callback_query(F.data.startswith("tasks:cat:"))
async def cb_task_list(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    category_str = cb.data.split(":")[2]
    category = None if category_str == "all" else TaskCategory(category_str)
    await _show_task_list(cb, session, user, category, offset=0)


@router.callback_query(F.data.startswith("tasks:page:"))
async def cb_task_page(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    parts = cb.data.split(":")
    category_str = parts[2]
    offset = int(parts[3])
    category = None if category_str == "all" else TaskCategory(category_str)
    await _show_task_list(cb, session, user, category, offset=offset)


async def _show_task_list(cb, session, user, category, offset):
    tasks = await crud.get_tasks(session, category=category, limit=PAGE_SIZE, offset=offset)
    all_tasks = await crud.get_tasks(session, category=category, limit=9999)
    total = len(all_tasks)
    cat_str = category.value if category else "all"
    label = CATEGORY_LABELS.get(category, "📋 Все задания") if category else "📋 Все задания"

    if not tasks:
        await cb.message.edit_text(f"{label}\n\nЗаданий пока нет.")
        await cb.answer()
        return

    await cb.message.edit_text(
        f"{label}\n\nВыберите задание:",
        reply_markup=tasks_list_keyboard(tasks, cat_str, offset, total, PAGE_SIZE),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("task:view:"))
async def cb_task_detail(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    task_id = int(cb.data.split(":")[2])
    task = await crud.get_task_by_id(session, task_id)
    if not task:
        await cb.answer("Задание не найдено.", show_alert=True)
        return

    can_submit, reason = await task_service.can_submit_task(session, user, task)
    text = format_task(task)
    if not can_submit:
        text += f"\n\n⚠️ <i>{h(reason)}</i>"

    await cb.message.edit_text(text, reply_markup=task_detail_keyboard(task, can_submit))
    await cb.answer()


@router.callback_query(F.data.startswith("task:submit:"))
async def cb_submit_start(cb: CallbackQuery, session: AsyncSession, user: User, state: FSMContext) -> None:
    task_id = int(cb.data.split(":")[2])
    task = await crud.get_task_by_id(session, task_id)
    if not task:
        await cb.answer("Задание не найдено.", show_alert=True)
        return

    can_submit, reason = await task_service.can_submit_task(session, user, task)
    if not can_submit:
        await cb.answer(reason, show_alert=True)
        return

    await state.update_data(task_id=task_id)

    if task.requires_photo:
        await state.set_state(SubmitTaskFSM.waiting_proof_photo)
        await cb.message.answer(
            f"📷 Отправьте фото как доказательство выполнения задания <b>{h(task.title)}</b>:",
            reply_markup=cancel_keyboard(),
        )
    elif task.requires_video:
        await state.set_state(SubmitTaskFSM.waiting_proof_video)
        await cb.message.answer(
            f"🎥 Отправьте видео как доказательство выполнения задания <b>{h(task.title)}</b>:",
            reply_markup=cancel_keyboard(),
        )
    elif task.requires_link:
        await state.set_state(SubmitTaskFSM.waiting_proof_link)
        hint = f"\n💡 Подсказка: {h(task.link_hint)}" if task.link_hint else ""
        await cb.message.answer(
            f"🔗 Отправьте ссылку как доказательство выполнения задания <b>{h(task.title)}</b>:{hint}",
            reply_markup=cancel_keyboard(),
        )
    else:
        await state.set_state(SubmitTaskFSM.waiting_proof_text)
        await cb.message.answer(
            f"✏️ Опишите, как вы выполнили задание <b>{h(task.title)}</b>:\n\nОтправьте текстовое описание:",
            reply_markup=cancel_keyboard(),
        )
    await cb.answer()


@router.message(SubmitTaskFSM.waiting_proof_text)
async def submit_text_proof(message: Message, session: AsyncSession, user: User, state: FSMContext) -> None:
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu(user.role.value))
        return
    data = await state.get_data()
    task = await crud.get_task_by_id(session, data["task_id"])
    sub = await task_service.submit_task(session, user, task, proof_text=message.text)
    await state.clear()
    await _confirm_submission(message, user, task, sub)


@router.message(SubmitTaskFSM.waiting_proof_photo, F.photo)
async def submit_photo_proof(message: Message, session: AsyncSession, user: User, state: FSMContext) -> None:
    data = await state.get_data()
    task = await crud.get_task_by_id(session, data["task_id"])
    sub = await task_service.submit_task(
        session, user, task,
        proof_text=message.caption or "",
        proof_photo_file_id=message.photo[-1].file_id,
    )
    await state.clear()
    await _confirm_submission(message, user, task, sub)


@router.message(SubmitTaskFSM.waiting_proof_video, F.video)
async def submit_video_proof(message: Message, session: AsyncSession, user: User, state: FSMContext) -> None:
    data = await state.get_data()
    task = await crud.get_task_by_id(session, data["task_id"])
    sub = await task_service.submit_task(
        session, user, task,
        proof_text=message.caption or "",
        proof_video_file_id=message.video.file_id,
    )
    await state.clear()
    await _confirm_submission(message, user, task, sub)


@router.message(SubmitTaskFSM.waiting_proof_link)
async def submit_link_proof(message: Message, session: AsyncSession, user: User, state: FSMContext) -> None:
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=main_menu(user.role.value))
        return
    data = await state.get_data()
    task = await crud.get_task_by_id(session, data["task_id"])
    sub = await task_service.submit_task(session, user, task, proof_link=message.text)
    await state.clear()
    await _confirm_submission(message, user, task, sub)


async def _confirm_submission(message, user, task, sub) -> None:
    from bot.database.models import TaskStatus
    if sub.status == TaskStatus.APPROVED:
        await message.answer(
            f"✅ <b>Задание выполнено!</b>\n\n"
            f"🎯 {h(task.title)}\n"
            f"✨ Начислено: <b>+{sub.xp_awarded} XP</b>",
            reply_markup=main_menu(user.role.value),
        )
    else:
        await message.answer(
            f"📤 <b>Заявка отправлена на проверку!</b>\n\n"
            f"🎯 {h(task.title)}\n"
            f"⏳ После одобрения вам начислится <b>+{task.xp_reward} XP</b>",
            reply_markup=main_menu(user.role.value),
        )
