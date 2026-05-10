"""Rate-limiting middleware using Redis."""
from typing import Callable, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message
from redis.asyncio import Redis


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, redis: Redis, rate_limit: float = 0.5):
        self._redis = redis
        self._rate = rate_limit  # seconds between allowed messages

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id if event.from_user else None
        if not user_id:
            return await handler(event, data)

        key = f"throttle:{user_id}"
        result = await self._redis.set(key, "1", px=int(self._rate * 1000), nx=True)
        if result is None:
            # Already set → user is flooding
            await event.answer("⏳ Слишком много запросов. Подождите немного.")
            return

        return await handler(event, data)
