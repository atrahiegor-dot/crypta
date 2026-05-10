"""Handler decorators for role checks."""
import functools
from typing import Callable

from aiogram.types import Message, CallbackQuery

from bot.database.models import UserRole


def require_role(*roles: UserRole):
    """Decorator: deny access if user doesn't have one of the required roles."""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(event, *args, **kwargs):
            user = kwargs.get("user") or (args[0] if args else None)
            # Try to find user in data dict (handler injection)
            if hasattr(event, "__class__") and "data" in kwargs:
                user = kwargs["data"].get("user")
            if not user or user.role not in roles:
                if isinstance(event, Message):
                    await event.answer("⛔ Недостаточно прав для этого действия.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("⛔ Недостаточно прав.", show_alert=True)
                return
            return await func(event, *args, **kwargs)
        return wrapper
    return decorator
