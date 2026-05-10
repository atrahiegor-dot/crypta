from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

REMOVE = ReplyKeyboardRemove()


def main_menu(role: str = "user") -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="🎯 Задания"), KeyboardButton(text="👤 Профиль")],
        [KeyboardButton(text="🏆 Рейтинг"), KeyboardButton(text="💰 Кошелёк")],
        [KeyboardButton(text="👥 Рефералы"), KeyboardButton(text="🏅 Достижения")],
        [KeyboardButton(text="📅 Ежедневный бонус")],
    ]
    if role in ("moderator", "developer"):
        buttons.append([KeyboardButton(text="🛡 Модерация")])
    if role == "developer":
        buttons.append([KeyboardButton(text="⚙️ Админ-панель")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
    )


def proof_keyboard(requires_photo: bool, requires_video: bool, requires_link: bool) -> ReplyKeyboardMarkup:
    rows = []
    if requires_photo:
        rows.append([KeyboardButton(text="📷 Прикрепить фото")])
    if requires_video:
        rows.append([KeyboardButton(text="🎥 Прикрепить видео")])
    if requires_link:
        rows.append([KeyboardButton(text="🔗 Ввести ссылку")])
    rows.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)
