"""
Middleware that resolves the current User ORM object from the database
and injects it into handler data as `user`. Also registers new users.
"""
from typing import Callable, Any, Awaitable
from datetime import datetime, timezone

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database import crud
from bot.database.models import UserRole


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        session: AsyncSession = data.get("session")

        # Extract Telegram user from event
        tg_user = None
        if isinstance(event, Update):
            for attr in ("message", "callback_query", "inline_query"):
                obj = getattr(event, attr, None)
                if obj and obj.from_user:
                    tg_user = obj.from_user
                    break

        if not tg_user or tg_user.is_bot:
            data["user"] = None
            return await handler(event, data)

        db_user = await crud.get_user_by_telegram_id(session, tg_user.id)

        if not db_user:
            # Determine role: developer if in ADMIN_IDS
            role = UserRole.DEVELOPER if tg_user.id in settings.ADMIN_IDS else UserRole.USER
            db_user = await crud.create_user(
                session,
                telegram_id=tg_user.id,
                first_name=tg_user.first_name,
                username=tg_user.username,
                last_name=tg_user.last_name,
                role=role,
            )
            await session.flush()
        else:
            # Keep profile data in sync
            db_user.first_name = tg_user.first_name
            db_user.username = tg_user.username
            db_user.last_name = tg_user.last_name
            db_user.last_activity = datetime.now(timezone.utc)

            # Ensure admin IDs always have developer role
            if tg_user.id in settings.ADMIN_IDS and db_user.role != UserRole.DEVELOPER:
                db_user.role = UserRole.DEVELOPER

        if db_user.is_banned:
            # Silently drop the update if user is banned
            data["user"] = db_user
            return  # Do not call handler

        data["user"] = db_user
        return await handler(event, data)
