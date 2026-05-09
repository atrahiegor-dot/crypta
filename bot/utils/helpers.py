"""Formatting and helper utilities (HTML parse mode)."""
from typing import Optional

from bot.database.models import UserRole, TaskDifficulty, AchievementType
from bot.services.xp_service import xp_for_next_level, xp_progress

# ─── Emoji maps ───────────────────────────────────────────────────────────────

ROLE_EMOJI = {
    UserRole.USER: "👤",
    UserRole.MODERATOR: "🛡",
    UserRole.DEVELOPER: "⚙️",
}

DIFFICULTY_EMOJI = {
    TaskDifficulty.EASY: "🟢",
    TaskDifficulty.MEDIUM: "🟡",
    TaskDifficulty.HARD: "🔴",
    TaskDifficulty.LEGENDARY: "👑",
}

ACHIEVEMENT_INFO = {
    AchievementType.FIRST_TASK: ("🎯", "Первое задание", "Выполнено первое задание"),
    AchievementType.TASKS_10: ("🔥", "10 заданий", "Выполнено 10 заданий"),
    AchievementType.TASKS_50: ("💪", "50 заданий", "Выполнено 50 заданий"),
    AchievementType.TASKS_100: ("🏆", "100 заданий", "Выполнено 100 заданий"),
    AchievementType.LEVEL_5: ("⭐", "Уровень 5", "Достигнут 5-й уровень"),
    AchievementType.LEVEL_10: ("🌟", "Уровень 10", "Достигнут 10-й уровень"),
    AchievementType.LEVEL_25: ("💎", "Уровень 25", "Достигнут 25-й уровень"),
    AchievementType.WALLET_CONNECTED: ("💰", "TON-кошелёк", "Подключён TON-кошелёк"),
    AchievementType.FIRST_REFERRAL: ("👋", "Первый реферал", "Приглашён первый пользователь"),
    AchievementType.REFERRALS_10: ("👥", "10 рефералов", "Приглашено 10 пользователей"),
    AchievementType.TOP_10_LEADERBOARD: ("🥇", "Топ-10", "Попадание в топ-10"),
    AchievementType.DAILY_STREAK_7: ("📅", "Серия 7 дней", "7 дней подряд"),
    AchievementType.DAILY_STREAK_30: ("🗓", "Серия 30 дней", "30 дней подряд"),
}


def h(text: str) -> str:
    """Escape HTML special characters."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def b(text: str) -> str:
    return f"<b>{h(text)}</b>"


def i(text: str) -> str:
    return f"<i>{h(text)}</i>"


def code(text: str) -> str:
    return f"<code>{h(text)}</code>"


def progress_bar(current: int, total: int, length: int = 10) -> str:
    if total == 0:
        return "▓" * length
    filled = min(length, int(current / total * length))
    return "▓" * filled + "░" * (length - filled)


def format_profile(user, rank: int) -> str:
    role_label = ROLE_EMOJI.get(user.role, "👤") + " " + user.role.value.capitalize()
    cur_xp, needed_xp = xp_progress(user.xp_points, user.level)
    bar = progress_bar(cur_xp, needed_xp)
    wallet_str = (
        code(f"{user.wallet_address[:6]}...{user.wallet_address[-4:]}")
        if user.wallet_address else "не подключён"
    )
    return (
        f"👤 <b>{h(user.display_name)}</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🎖 Роль: {role_label}\n"
        f"🏆 Уровень: <b>{user.level}</b>\n"
        f"✨ XP: <b>{user.xp_points:,}</b>\n"
        f"📊 Прогресс: {bar} {cur_xp}/{needed_xp}\n"
        f"🥇 Место в рейтинге: <b>#{rank}</b>\n"
        f"💰 Кошелёк: {wallet_str}\n"
        f"🔥 Серия: <b>{user.daily_streak}</b> дней\n"
        f"👥 Рефералов: __REF__\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📅 Регистрация: {user.created_at.strftime('%d.%m.%Y')}"
    )


def format_task(task) -> str:
    diff_emoji = DIFFICULTY_EMOJI.get(task.difficulty, "")
    lines = [
        f"<b>{h(task.title)}</b>",
        "",
        h(task.description),
        "",
        "━━━━━━━━━━━━━━━━",
        f"💎 Сложность: {diff_emoji} {task.difficulty.value}",
        f"✨ Награда: <b>+{task.xp_reward} XP</b>",
    ]
    if float(task.tt_reward) > 0:
        lines.append(f"🪙 TT-токены: +{task.tt_reward}")
    reqs = []
    if task.requires_photo:
        reqs.append("📷 Фото")
    if task.requires_video:
        reqs.append("🎥 Видео")
    if task.requires_link:
        reqs.append("🔗 Ссылка")
    if reqs:
        lines.append(f"📎 Требуется: {', '.join(reqs)}")
    if task.requires_moderation:
        lines.append("🔍 Проверяется модератором")
    else:
        lines.append("⚡ Автоматическая проверка")
    return "\n".join(lines)


def format_leaderboard(entries: list, viewer_id: Optional[int] = None) -> str:
    if not entries:
        return "Таблица пуста. Выполняйте задания, чтобы попасть сюда!"
    lines = ["🏆 <b>Таблица лидеров</b>\n"]
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    for rank, user in entries:
        medal = medals.get(rank, f"{rank}.")
        marker = " ◀️ <b>вы</b>" if user.telegram_id == viewer_id else ""
        lines.append(f"{medal} {h(user.display_name)} — {user.xp_points:,} XP{marker}")
    return "\n".join(lines)


def short_address(address: str) -> str:
    if not address or len(address) < 10:
        return address
    return f"{address[:6]}...{address[-4:]}"


# Keep for backward compat
def escape_md(text: str) -> str:
    return h(text)
