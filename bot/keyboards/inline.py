from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database.models import Task, TaskCategory, TaskDifficulty


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _btn(text: str, callback: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=callback)


def _url_btn(text: str, url: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, url=url)


# ─── Tasks ────────────────────────────────────────────────────────────────────

CATEGORY_LABELS = {
    TaskCategory.SOCIAL: "📢 Социальные",
    TaskCategory.COMMUNITY: "👥 Сообщество",
    TaskCategory.DEVELOPMENT: "💻 Разработка",
    TaskCategory.CREATIVE: "🎨 Творческие",
    TaskCategory.SPECIAL: "⭐ Специальные",
}

DIFFICULTY_LABELS = {
    TaskDifficulty.EASY: "🟢 Лёгкое",
    TaskDifficulty.MEDIUM: "🟡 Среднее",
    TaskDifficulty.HARD: "🔴 Сложное",
    TaskDifficulty.LEGENDARY: "👑 Легендарное",
}


def task_categories_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat, label in CATEGORY_LABELS.items():
        builder.button(text=label, callback_data=f"tasks:cat:{cat.value}")
    builder.button(text="📋 Все задания", callback_data="tasks:cat:all")
    builder.adjust(2)
    return builder.as_markup()


def tasks_list_keyboard(
    tasks: list,
    category: str,
    offset: int,
    total: int,
    page_size: int = 5,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for task in tasks:
        diff = DIFFICULTY_LABELS.get(task.difficulty, "")
        builder.button(
            text=f"{diff} {task.title} (+{task.xp_reward} XP)",
            callback_data=f"task:view:{task.id}",
        )
    builder.adjust(1)

    nav_row = []
    if offset > 0:
        nav_row.append(_btn("◀️ Назад", f"tasks:page:{category}:{max(0, offset - page_size)}"))
    if offset + page_size < total:
        nav_row.append(_btn("Вперёд ▶️", f"tasks:page:{category}:{offset + page_size}"))
    if nav_row:
        builder.row(*nav_row)

    builder.row(_btn("🔙 Категории", "tasks:categories"))
    return builder.as_markup()


def task_detail_keyboard(task: Task, can_submit: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if can_submit:
        builder.button(text="✅ Выполнить задание", callback_data=f"task:submit:{task.id}")
    builder.button(text="🔙 Назад", callback_data=f"tasks:cat:{task.category.value}")
    builder.adjust(1)
    return builder.as_markup()


# ─── Wallet ───────────────────────────────────────────────────────────────────

def wallet_connect_keyboard(connect_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(_url_btn("📱 Открыть Tonkeeper", connect_url))
    builder.row(_btn("✅ Проверить подключение", "wallet:check"))
    builder.row(_btn("❌ Отмена", "wallet:cancel"))
    return builder.as_markup()


def wallet_connected_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔌 Отключить кошелёк", callback_data="wallet:disconnect")
    builder.adjust(1)
    return builder.as_markup()


# ─── Leaderboard ──────────────────────────────────────────────────────────────

def leaderboard_keyboard(period: str = "all") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    periods = [("🌐 Всё время", "all"), ("📅 Неделя", "week"), ("📆 Месяц", "month")]
    for label, p in periods:
        prefix = "▶️ " if p == period else ""
        builder.button(text=f"{prefix}{label}", callback_data=f"lb:{p}")
    builder.adjust(3)
    return builder.as_markup()


# ─── Profile ──────────────────────────────────────────────────────────────────

def profile_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🏅 Мои достижения", callback_data="profile:achievements")
    builder.button(text="📋 Мои заявки", callback_data="profile:submissions")
    builder.adjust(2)
    return builder.as_markup()


# ─── Moderation ───────────────────────────────────────────────────────────────

def moderation_submission_keyboard(submission_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Одобрить", callback_data=f"mod:approve:{submission_id}")
    builder.button(text="❌ Отклонить", callback_data=f"mod:reject:{submission_id}")
    builder.button(text="⏭ Следующая", callback_data="mod:next")
    builder.adjust(2, 1)
    return builder.as_markup()


def moderation_reject_reasons_keyboard(submission_id: int) -> InlineKeyboardMarkup:
    reasons = [
        ("Недостаточно доказательств", "proof"),
        ("Неверный формат", "format"),
        ("Задание не выполнено", "incomplete"),
        ("Нарушение правил", "rules"),
    ]
    builder = InlineKeyboardBuilder()
    for label, code in reasons:
        builder.button(text=label, callback_data=f"mod:reject_reason:{submission_id}:{code}")
    builder.button(text="✏️ Своя причина", callback_data=f"mod:reject_custom:{submission_id}")
    builder.button(text="◀️ Назад", callback_data=f"mod:back:{submission_id}")
    builder.adjust(2, 2, 1, 1)
    return builder.as_markup()


# ─── Admin ────────────────────────────────────────────────────────────────────

def admin_main_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Создать задание", callback_data="admin:task:create")
    builder.button(text="📋 Список заданий", callback_data="admin:task:list:0")
    builder.button(text="👥 Пользователи", callback_data="admin:users:search")
    builder.button(text="🎉 Бонусные события", callback_data="admin:bonus:list")
    builder.button(text="📊 Статистика", callback_data="admin:stats")
    builder.adjust(2, 2, 1)
    return builder.as_markup()


def admin_task_keyboard(task_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Редактировать", callback_data=f"admin:task:edit:{task_id}")
    builder.button(text="🔴 Деактивировать", callback_data=f"admin:task:toggle:{task_id}")
    builder.button(text="◀️ Назад", callback_data="admin:task:list:0")
    builder.adjust(2, 1)
    return builder.as_markup()


def admin_user_keyboard(user_id: int, is_banned: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if is_banned:
        builder.button(text="✅ Разбанить", callback_data=f"admin:user:unban:{user_id}")
    else:
        builder.button(text="🚫 Забанить", callback_data=f"admin:user:ban:{user_id}")
    builder.button(text="🛡 Сделать модератором", callback_data=f"admin:user:role:moderator:{user_id}")
    builder.button(text="👤 Сделать пользователем", callback_data=f"admin:user:role:user:{user_id}")
    builder.adjust(1)
    return builder.as_markup()


def confirm_keyboard(confirm_cb: str, cancel_cb: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data=confirm_cb)
    builder.button(text="❌ Отмена", callback_data=cancel_cb)
    builder.adjust(2)
    return builder.as_markup()
