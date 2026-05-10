"""Admin panel — full CRUD for tasks, users, bonus events."""
from datetime import datetime, timezone, timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import crud
from bot.database.models import User, UserRole, TaskCategory, TaskDifficulty, BonusEvent
from bot.keyboards.inline import (
    admin_main_keyboard, admin_task_keyboard,
    admin_user_keyboard, confirm_keyboard,
)
from bot.keyboards.reply import cancel_keyboard
from bot.utils.helpers import h, code

router = Router(name="admin")
PAGE_SIZE = 5


def _is_dev(user: User) -> bool:
    return user.role == UserRole.DEVELOPER


# ─── FSM States ───────────────────────────────────────────────────────────────

class CreateTaskFSM(StatesGroup):
    title = State()
    description = State()
    category = State()
    difficulty = State()
    xp_reward = State()
    requires_moderation = State()
    requires_photo = State()
    requires_link = State()
    confirm = State()


class EditTaskFSM(StatesGroup):
    choose_field = State()
    new_value = State()


class SearchUserFSM(StatesGroup):
    query = State()


class BanUserFSM(StatesGroup):
    reason = State()


class BonusEventFSM(StatesGroup):
    name = State()
    description = State()
    xp_multiplier = State()
    duration_hours = State()
    confirm = State()


# ─── Main panel ───────────────────────────────────────────────────────────────

@router.message(Command("admin"))
@router.message(F.text == "⚙️ Админ-панель")
async def cmd_admin(message: Message, user: User) -> None:
    if not _is_dev(user):
        await message.answer("⛔ Недостаточно прав.")
        return
    await message.answer(
        f"⚙️ <b>Административная панель</b>\n"
        f"Добро пожаловать, <b>{h(user.first_name)}</b>!",
        reply_markup=admin_main_keyboard(),
    )


@router.callback_query(F.data == "admin:main")
async def cb_admin_main(cb: CallbackQuery, user: User) -> None:
    if not _is_dev(user):
        await cb.answer("⛔", show_alert=True)
        return
    await cb.message.edit_text(
        "⚙️ <b>Административная панель</b>",
        reply_markup=admin_main_keyboard(),
    )
    await cb.answer()


# ─── Statistics ───────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:stats")
async def cb_stats(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    if not _is_dev(user):
        await cb.answer("⛔", show_alert=True)
        return
    total_users = await crud.get_total_users_count(session)
    total_tasks = await crud.get_tasks_count(session)
    pending = await crud.get_pending_submissions_count(session)
    active_event = await crud.get_active_bonus_event(session)

    event_line = ""
    if active_event:
        event_line = f"\n🎉 Активное событие: <b>{h(active_event.name)}</b> (x{active_event.xp_multiplier} XP)"

    await cb.message.edit_text(
        f"📊 <b>Статистика платформы</b>\n\n"
        f"👤 Пользователей: <b>{total_users}</b>\n"
        f"🎯 Активных заданий: <b>{total_tasks}</b>\n"
        f"⏳ Заявок на проверке: <b>{pending}</b>"
        f"{event_line}",
        reply_markup=_back_to_admin(),
    )
    await cb.answer()


# ─── Task list ────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin:task:list:"))
async def cb_task_list(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    if not _is_dev(user):
        await cb.answer("⛔", show_alert=True)
        return
    offset = int(cb.data.split(":")[3])
    tasks = await crud.get_tasks(session, limit=PAGE_SIZE, offset=offset)
    all_tasks = await crud.get_tasks(session, limit=9999)
    total = len(all_tasks)

    if not tasks:
        await cb.message.edit_text(
            "📋 Заданий нет. Создайте первое!",
            reply_markup=_task_list_nav(offset, total, with_create=True),
        )
        await cb.answer()
        return

    builder = InlineKeyboardBuilder()
    for t in tasks:
        icon = "✅" if t.is_active else "❌"
        builder.button(
            text=f"{icon} [{t.id}] {t.title[:28]}",
            callback_data=f"admin:task:detail:{t.id}",
        )
    builder.adjust(1)

    nav = []
    if offset > 0:
        nav.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"admin:task:list:{offset - PAGE_SIZE}"))
    if offset + PAGE_SIZE < total:
        nav.append(InlineKeyboardButton(text="Вперёд ▶️", callback_data=f"admin:task:list:{offset + PAGE_SIZE}"))
    if nav:
        builder.row(*nav)
    builder.row(InlineKeyboardButton(text="➕ Создать задание", callback_data="admin:task:create"))
    builder.row(InlineKeyboardButton(text="◀️ Главная", callback_data="admin:main"))

    await cb.message.edit_text(
        f"📋 <b>Задания</b> ({offset + 1}–{min(offset + PAGE_SIZE, total)} из {total}):",
        reply_markup=builder.as_markup(),
    )
    await cb.answer()


@router.callback_query(F.data.startswith("admin:task:detail:"))
async def cb_task_detail(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    if not _is_dev(user):
        await cb.answer("⛔", show_alert=True)
        return
    task_id = int(cb.data.split(":")[3])
    task = await crud.get_task_by_id(session, task_id)
    if not task:
        await cb.answer("Задание не найдено.", show_alert=True)
        return

    reqs = []
    if task.requires_photo: reqs.append("📷 фото")
    if task.requires_video: reqs.append("🎥 видео")
    if task.requires_link: reqs.append("🔗 ссылка")
    req_str = ", ".join(reqs) if reqs else "нет"

    text = (
        f"🎯 <b>{h(task.title)}</b> {code(f'#{task.id}')}\n\n"
        f"📄 {h(task.description)}\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📂 Категория: <b>{task.category.value}</b>\n"
        f"💎 Сложность: <b>{task.difficulty.value}</b>\n"
        f"✨ XP: <b>{task.xp_reward}</b>\n"
        f"🔍 Модерация: {'да' if task.requires_moderation else 'нет'}\n"
        f"📎 Доказательства: {req_str}\n"
        f"📊 Выполнений: <b>{task.completions_count}</b>\n"
        f"🟢 Активно: {'✅ да' if task.is_active else '❌ нет'}"
    )
    await cb.message.edit_text(text, reply_markup=admin_task_keyboard(task.id))
    await cb.answer()


@router.callback_query(F.data.startswith("admin:task:toggle:"))
async def cb_task_toggle(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    if not _is_dev(user):
        await cb.answer("⛔", show_alert=True)
        return
    task_id = int(cb.data.split(":")[3])
    task = await crud.get_task_by_id(session, task_id)
    if task:
        task.is_active = not task.is_active
        status = "активировано ✅" if task.is_active else "деактивировано ❌"
        await cb.answer(f"Задание {status}.")
        await cb.message.edit_reply_markup(reply_markup=admin_task_keyboard(task.id))


# ─── Task creation FSM ────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:task:create")
async def cb_task_create(cb: CallbackQuery, user: User, state: FSMContext) -> None:
    if not _is_dev(user):
        await cb.answer("⛔", show_alert=True)
        return
    await state.set_state(CreateTaskFSM.title)
    await cb.message.answer(
        "📝 <b>Создание задания</b>\n\nШаг 1/8 — Введите <b>название</b> задания:",
        reply_markup=cancel_keyboard(),
    )
    await cb.answer()


@router.message(CreateTaskFSM.title)
async def fsm_title(message: Message, state: FSMContext) -> None:
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.")
        return
    await state.update_data(title=message.text)
    await state.set_state(CreateTaskFSM.description)
    await message.answer("Шаг 2/8 — Введите <b>описание</b> задания:")


@router.message(CreateTaskFSM.description)
async def fsm_desc(message: Message, state: FSMContext) -> None:
    if message.text == "❌ Отмена":
        await state.clear(); await message.answer("Отменено."); return
    await state.update_data(description=message.text)
    await state.set_state(CreateTaskFSM.category)
    cats = " | ".join(f"<code>{c.value}</code>" for c in TaskCategory)
    await message.answer(f"Шаг 3/8 — Выберите <b>категорию</b>:\n{cats}")


@router.message(CreateTaskFSM.category)
async def fsm_category(message: Message, state: FSMContext) -> None:
    if message.text == "❌ Отмена":
        await state.clear(); await message.answer("Отменено."); return
    try:
        cat = TaskCategory(message.text.lower())
    except ValueError:
        await message.answer(f"❌ Неверная категория. Введите одно из: {', '.join(c.value for c in TaskCategory)}")
        return
    await state.update_data(category=cat.value)
    await state.set_state(CreateTaskFSM.difficulty)
    diffs = " | ".join(f"<code>{d.value}</code>" for d in TaskDifficulty)
    await message.answer(f"Шаг 4/8 — Выберите <b>сложность</b>:\n{diffs}")


@router.message(CreateTaskFSM.difficulty)
async def fsm_difficulty(message: Message, state: FSMContext) -> None:
    if message.text == "❌ Отмена":
        await state.clear(); await message.answer("Отменено."); return
    try:
        diff = TaskDifficulty(message.text.lower())
    except ValueError:
        await message.answer(f"❌ Неверная сложность. Введите: {', '.join(d.value for d in TaskDifficulty)}")
        return
    await state.update_data(difficulty=diff.value)
    await state.set_state(CreateTaskFSM.xp_reward)
    await message.answer("Шаг 5/8 — Введите количество <b>XP</b> за выполнение:")


@router.message(CreateTaskFSM.xp_reward)
async def fsm_xp(message: Message, state: FSMContext) -> None:
    if message.text == "❌ Отмена":
        await state.clear(); await message.answer("Отменено."); return
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("❌ Введите положительное целое число.")
        return
    await state.update_data(xp_reward=int(message.text))
    await state.set_state(CreateTaskFSM.requires_moderation)
    await message.answer("Шаг 6/8 — Требуется ли <b>проверка модератором</b>? (да / нет)")


@router.message(CreateTaskFSM.requires_moderation)
async def fsm_mod(message: Message, state: FSMContext) -> None:
    await state.update_data(requires_moderation=message.text.lower() in ("да", "yes", "1", "true"))
    await state.set_state(CreateTaskFSM.requires_photo)
    await message.answer("Шаг 7/8 — Требуется ли прикрепить <b>фото</b>? (да / нет)")


@router.message(CreateTaskFSM.requires_photo)
async def fsm_photo(message: Message, state: FSMContext) -> None:
    await state.update_data(requires_photo=message.text.lower() in ("да", "yes", "1", "true"))
    await state.set_state(CreateTaskFSM.requires_link)
    await message.answer("Шаг 8/8 — Требуется ли ввести <b>ссылку</b>? (да / нет)")


@router.message(CreateTaskFSM.requires_link)
async def fsm_link(message: Message, state: FSMContext) -> None:
    await state.update_data(requires_link=message.text.lower() in ("да", "yes", "1", "true"))
    data = await state.get_data()
    preview = (
        f"📋 <b>Предпросмотр:</b>\n\n"
        f"📌 <b>{h(data['title'])}</b>\n"
        f"📄 {h(data['description'][:150])}\n\n"
        f"📂 Категория: <b>{data['category']}</b>\n"
        f"💎 Сложность: <b>{data['difficulty']}</b>\n"
        f"✨ XP: <b>{data['xp_reward']}</b>\n"
        f"🔍 Модерация: {'да' if data['requires_moderation'] else 'нет'}\n"
        f"📷 Фото: {'да' if data.get('requires_photo') else 'нет'}\n"
        f"🔗 Ссылка: {'да' if data.get('requires_link') else 'нет'}\n\n"
        f"Создать задание?"
    )
    await state.set_state(CreateTaskFSM.confirm)
    await message.answer(preview, reply_markup=confirm_keyboard("admin:task:confirm", "admin:task:cancel_fsm"))


@router.callback_query(F.data == "admin:task:confirm")
async def cb_task_confirm(cb: CallbackQuery, session: AsyncSession, user: User, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    task = await crud.create_task(
        session,
        title=data["title"],
        description=data["description"],
        category=TaskCategory(data["category"]),
        difficulty=TaskDifficulty(data["difficulty"]),
        xp_reward=data["xp_reward"],
        requires_moderation=data["requires_moderation"],
        requires_photo=data.get("requires_photo", False),
        requires_link=data.get("requires_link", False),
        created_by_id=user.id,
    )
    await cb.message.edit_text(
        f"✅ Задание <b>{h(task.title)}</b> создано!\n"
        f"🆔 ID: {code(str(task.id))}",
        reply_markup=_back_to_admin(),
    )
    await cb.answer("✅ Создано!")


@router.callback_query(F.data == "admin:task:cancel_fsm")
async def cb_task_cancel(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cb.message.edit_text("Отменено.", reply_markup=admin_main_keyboard())
    await cb.answer()


# ─── Task edit ────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("admin:task:edit:"))
async def cb_task_edit(cb: CallbackQuery, user: User, state: FSMContext) -> None:
    if not _is_dev(user):
        await cb.answer("⛔", show_alert=True)
        return
    task_id = int(cb.data.split(":")[3])
    await state.set_state(EditTaskFSM.choose_field)
    await state.update_data(task_id=task_id)

    builder = InlineKeyboardBuilder()
    fields = [
        ("📌 Название", "title"), ("📄 Описание", "description"),
        ("✨ XP", "xp_reward"), ("🔍 Модерация", "requires_moderation"),
    ]
    for label, field in fields:
        builder.button(text=label, callback_data=f"admin:task:editfield:{task_id}:{field}")
    builder.button(text="❌ Отмена", callback_data=f"admin:task:detail:{task_id}")
    builder.adjust(2, 2, 1)
    await cb.message.edit_text("Что изменить?", reply_markup=builder.as_markup())
    await cb.answer()


@router.callback_query(F.data.startswith("admin:task:editfield:"))
async def cb_task_editfield(cb: CallbackQuery, state: FSMContext) -> None:
    parts = cb.data.split(":")
    task_id, field = int(parts[3]), parts[4]
    await state.set_state(EditTaskFSM.new_value)
    await state.update_data(task_id=task_id, field=field)
    prompts = {
        "title": "Введите новое <b>название</b>:",
        "description": "Введите новое <b>описание</b>:",
        "xp_reward": "Введите новое количество <b>XP</b> (число):",
        "requires_moderation": "Требуется модерация? (<b>да</b> / <b>нет</b>):",
    }
    await cb.message.answer(prompts.get(field, "Введите новое значение:"))
    await cb.answer()


@router.message(EditTaskFSM.new_value)
async def fsm_edit_value(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    field = data["field"]
    task_id = data["task_id"]
    value = message.text

    if field == "xp_reward":
        if not value.isdigit():
            await message.answer("Введите целое число.")
            return
        value = int(value)
    elif field == "requires_moderation":
        value = value.lower() in ("да", "yes", "1", "true")

    await crud.update_task(session, task_id, **{field: value})
    await state.clear()
    await message.answer(f"✅ Поле обновлено.")


# ─── User management ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:users:search")
async def cb_user_search(cb: CallbackQuery, user: User, state: FSMContext) -> None:
    if not _is_dev(user):
        await cb.answer("⛔", show_alert=True)
        return
    await state.set_state(SearchUserFSM.query)
    await cb.message.answer("🔍 Введите <b>username</b>, имя или <b>Telegram ID</b>:")
    await cb.answer()


@router.message(SearchUserFSM.query)
async def fsm_user_search(message: Message, session: AsyncSession, state: FSMContext) -> None:
    await state.clear()
    results = await crud.search_users(session, message.text, limit=10)
    if not results:
        await message.answer("Пользователи не найдены.")
        return
    builder = InlineKeyboardBuilder()
    for u in results:
        role_icon = {"developer": "⚙️", "moderator": "🛡", "user": "👤"}.get(u.role.value, "👤")
        builder.button(
            text=f"{role_icon} {u.display_name} | Ур.{u.level} | {u.xp_points} XP",
            callback_data=f"admin:user:detail:{u.id}",
        )
    builder.adjust(1)
    await message.answer(f"Найдено: <b>{len(results)}</b>", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("admin:user:detail:"))
async def cb_user_detail(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    if not _is_dev(user):
        await cb.answer("⛔", show_alert=True)
        return
    target_id = int(cb.data.split(":")[3])
    target = await crud.get_user_by_id(session, target_id)
    if not target:
        await cb.answer("Не найдено.", show_alert=True)
        return
    ref_count = await crud.get_referral_count(session, target_id)
    role_icon = {"developer": "⚙️", "moderator": "🛡", "user": "👤"}.get(target.role.value, "👤")
    text = (
        f"👤 <b>{h(target.display_name)}</b>\n\n"
        f"🆔 TG ID: {code(str(target.telegram_id))}\n"
        f"{role_icon} Роль: <b>{target.role.value}</b>\n"
        f"✨ XP: <b>{target.xp_points:,}</b>\n"
        f"📊 Уровень: <b>{target.level}</b>\n"
        f"👥 Рефералов: <b>{ref_count}</b>\n"
        f"🔥 Серия: <b>{target.daily_streak}</b> дней\n"
        f"🚫 Заблокирован: {'<b>ДА</b>' if target.is_banned else 'нет'}\n"
        f"📅 Регистрация: {target.created_at.strftime('%d.%m.%Y %H:%M')}"
    )
    await cb.message.edit_text(text, reply_markup=admin_user_keyboard(target.id, target.is_banned))
    await cb.answer()


@router.callback_query(F.data.startswith("admin:user:ban:"))
async def cb_user_ban(cb: CallbackQuery, user: User, state: FSMContext) -> None:
    if not _is_dev(user):
        await cb.answer("⛔", show_alert=True)
        return
    target_id = int(cb.data.split(":")[3])
    await state.set_state(BanUserFSM.reason)
    await state.update_data(target_id=target_id)
    await cb.message.answer("📝 Введите причину бана:")
    await cb.answer()


@router.message(BanUserFSM.reason)
async def fsm_ban_reason(message: Message, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    await crud.ban_user(session, data["target_id"], message.text)
    target = await crud.get_user_by_id(session, data["target_id"])
    await message.answer(
        f"🚫 Пользователь <b>{h(target.display_name)}</b> заблокирован.\n"
        f"Причина: {h(message.text)}"
    )


@router.callback_query(F.data.startswith("admin:user:unban:"))
async def cb_user_unban(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    if not _is_dev(user):
        await cb.answer("⛔", show_alert=True)
        return
    target_id = int(cb.data.split(":")[3])
    await crud.unban_user(session, target_id)
    target = await crud.get_user_by_id(session, target_id)
    await cb.answer("✅ Пользователь разбанен.")
    await cb.message.edit_reply_markup(reply_markup=admin_user_keyboard(target_id, target.is_banned))


@router.callback_query(F.data.startswith("admin:user:role:"))
async def cb_user_role(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    if not _is_dev(user):
        await cb.answer("⛔", show_alert=True)
        return
    parts = cb.data.split(":")
    role_str, target_id = parts[3], int(parts[4])
    try:
        role = UserRole(role_str)
    except ValueError:
        await cb.answer("Неверная роль.", show_alert=True)
        return
    await crud.set_user_role(session, target_id, role)
    target = await crud.get_user_by_id(session, target_id)
    await cb.answer(f"✅ Роль изменена на {role.value}.")
    # Refresh detail view
    await cb.message.edit_reply_markup(reply_markup=admin_user_keyboard(target_id, target.is_banned))


# ─── Bonus Events ─────────────────────────────────────────────────────────────

@router.callback_query(F.data == "admin:bonus:list")
async def cb_bonus_list(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    if not _is_dev(user):
        await cb.answer("⛔", show_alert=True)
        return
    events = await crud.get_all_bonus_events(session)
    now = datetime.now(timezone.utc)

    if not events:
        builder = InlineKeyboardBuilder()
        builder.button(text="➕ Создать событие", callback_data="admin:bonus:create")
        builder.button(text="◀️ Назад", callback_data="admin:main")
        builder.adjust(1)
        await cb.message.edit_text("🎉 <b>Бонусные события</b>\n\nСобытий нет.", reply_markup=builder.as_markup())
        await cb.answer()
        return

    builder = InlineKeyboardBuilder()
    for ev in events[:10]:
        active = ev.starts_at <= now <= ev.ends_at and ev.is_active
        icon = "🟢" if active else "⚫"
        builder.button(
            text=f"{icon} {ev.name} (x{ev.xp_multiplier})",
            callback_data=f"admin:bonus:detail:{ev.id}",
        )
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="➕ Создать событие", callback_data="admin:bonus:create"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin:main"))

    await cb.message.edit_text("🎉 <b>Бонусные события</b>", reply_markup=builder.as_markup())
    await cb.answer()


@router.callback_query(F.data.startswith("admin:bonus:detail:"))
async def cb_bonus_detail(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    if not _is_dev(user):
        await cb.answer("⛔", show_alert=True)
        return
    from sqlalchemy import select
    event_id = int(cb.data.split(":")[3])
    result = await session.execute(select(BonusEvent).where(BonusEvent.id == event_id))
    ev = result.scalar_one_or_none()
    if not ev:
        await cb.answer("Не найдено.", show_alert=True)
        return
    now = datetime.now(timezone.utc)
    active = ev.starts_at <= now <= ev.ends_at and ev.is_active
    text = (
        f"🎉 <b>{h(ev.name)}</b>\n\n"
        f"📝 {h(ev.description or '—')}\n\n"
        f"✨ Множитель XP: <b>x{ev.xp_multiplier}</b>\n"
        f"📅 Начало: {ev.starts_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"📅 Конец: {ev.ends_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"🟢 Активно: {'да' if active else 'нет'}"
    )
    builder = InlineKeyboardBuilder()
    toggle_label = "🔴 Деактивировать" if ev.is_active else "🟢 Активировать"
    builder.button(text=toggle_label, callback_data=f"admin:bonus:toggle:{ev.id}")
    builder.button(text="◀️ Назад", callback_data="admin:bonus:list")
    builder.adjust(1)
    await cb.message.edit_text(text, reply_markup=builder.as_markup())
    await cb.answer()


@router.callback_query(F.data.startswith("admin:bonus:toggle:"))
async def cb_bonus_toggle(cb: CallbackQuery, session: AsyncSession, user: User) -> None:
    if not _is_dev(user):
        await cb.answer("⛔", show_alert=True)
        return
    from sqlalchemy import select
    event_id = int(cb.data.split(":")[3])
    result = await session.execute(select(BonusEvent).where(BonusEvent.id == event_id))
    ev = result.scalar_one_or_none()
    if ev:
        ev.is_active = not ev.is_active
        await cb.answer("Статус изменён.")
        await cb.message.edit_reply_markup(
            reply_markup=_bonus_toggle_kb(ev.id, ev.is_active)
        )


def _bonus_toggle_kb(ev_id: int, is_active: bool) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    label = "🔴 Деактивировать" if is_active else "🟢 Активировать"
    builder.button(text=label, callback_data=f"admin:bonus:toggle:{ev_id}")
    builder.button(text="◀️ Назад", callback_data="admin:bonus:list")
    builder.adjust(1)
    return builder.as_markup()


@router.callback_query(F.data == "admin:bonus:create")
async def cb_bonus_create(cb: CallbackQuery, user: User, state: FSMContext) -> None:
    if not _is_dev(user):
        await cb.answer("⛔", show_alert=True)
        return
    await state.set_state(BonusEventFSM.name)
    await cb.message.answer(
        "🎉 <b>Создание бонусного события</b>\n\nВведите <b>название</b> события:",
        reply_markup=cancel_keyboard(),
    )
    await cb.answer()


@router.message(BonusEventFSM.name)
async def bonus_fsm_name(message: Message, state: FSMContext) -> None:
    if message.text == "❌ Отмена":
        await state.clear(); await message.answer("Отменено."); return
    await state.update_data(name=message.text)
    await state.set_state(BonusEventFSM.description)
    await message.answer("Введите <b>описание</b> (или — чтобы пропустить):")


@router.message(BonusEventFSM.description)
async def bonus_fsm_desc(message: Message, state: FSMContext) -> None:
    if message.text == "❌ Отмена":
        await state.clear(); await message.answer("Отменено."); return
    await state.update_data(description="" if message.text == "—" else message.text)
    await state.set_state(BonusEventFSM.xp_multiplier)
    await message.answer("Введите <b>множитель XP</b> (например: 2 или 1.5):")


@router.message(BonusEventFSM.xp_multiplier)
async def bonus_fsm_multiplier(message: Message, state: FSMContext) -> None:
    if message.text == "❌ Отмена":
        await state.clear(); await message.answer("Отменено."); return
    try:
        mult = float(message.text.replace(",", "."))
        assert 0.1 <= mult <= 10
    except Exception:
        await message.answer("❌ Введите число от 0.1 до 10 (например: 2 или 1.5)")
        return
    await state.update_data(xp_multiplier=mult)
    await state.set_state(BonusEventFSM.duration_hours)
    await message.answer("Введите <b>длительность в часах</b> (например: 24):")


@router.message(BonusEventFSM.duration_hours)
async def bonus_fsm_duration(message: Message, state: FSMContext) -> None:
    if message.text == "❌ Отмена":
        await state.clear(); await message.answer("Отменено."); return
    if not message.text.isdigit() or int(message.text) <= 0:
        await message.answer("❌ Введите целое число часов.")
        return
    hours = int(message.text)
    await state.update_data(duration_hours=hours)
    data = await state.get_data()
    now = datetime.now(timezone.utc)
    ends = now + timedelta(hours=hours)
    preview = (
        f"🎉 <b>Предпросмотр события:</b>\n\n"
        f"📌 Название: <b>{h(data['name'])}</b>\n"
        f"✨ Множитель XP: <b>x{data['xp_multiplier']}</b>\n"
        f"⏱ Длительность: <b>{hours} ч</b>\n"
        f"📅 Начало: сейчас\n"
        f"📅 Конец: {ends.strftime('%d.%m.%Y %H:%M')} UTC\n\n"
        f"Создать событие?"
    )
    await state.set_state(BonusEventFSM.confirm)
    await message.answer(preview, reply_markup=confirm_keyboard("admin:bonus:confirm", "admin:bonus:cancel_fsm"))


@router.callback_query(F.data == "admin:bonus:confirm")
async def cb_bonus_confirm(cb: CallbackQuery, session: AsyncSession, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    now = datetime.now(timezone.utc)
    ends = now + timedelta(hours=data["duration_hours"])
    from decimal import Decimal
    ev = BonusEvent(
        name=data["name"],
        description=data.get("description", ""),
        xp_multiplier=Decimal(str(data["xp_multiplier"])),
        is_active=True,
        starts_at=now,
        ends_at=ends,
    )
    session.add(ev)
    await session.flush()
    await cb.message.edit_text(
        f"✅ Бонусное событие <b>{h(ev.name)}</b> запущено!\n"
        f"Множитель XP: <b>x{ev.xp_multiplier}</b> на {data['duration_hours']} часов.",
        reply_markup=_back_to_admin(),
    )
    await cb.answer("✅ Запущено!")


@router.callback_query(F.data == "admin:bonus:cancel_fsm")
async def cb_bonus_cancel(cb: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await cb.message.edit_text("Отменено.", reply_markup=admin_main_keyboard())
    await cb.answer()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _back_to_admin():
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Главная панель", callback_data="admin:main")
    return builder.as_markup()


def _task_list_nav(offset: int, total: int, with_create: bool = False):
    builder = InlineKeyboardBuilder()
    if with_create:
        builder.button(text="➕ Создать задание", callback_data="admin:task:create")
    builder.button(text="◀️ Главная", callback_data="admin:main")
    builder.adjust(1)
    return builder.as_markup()
