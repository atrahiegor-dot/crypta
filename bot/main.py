"""Bot entry point."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage as FSMRedisStorage

from bot.config import settings
from bot.database.base import engine, Base
from bot.handlers import setup_routers
from bot.middlewares import DatabaseMiddleware, AuthMiddleware, ThrottlingMiddleware
from bot.services.ton_connect import ton_connect_service
from bot.services.manifest_server import start_manifest_server, stop_manifest_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _build_redis():
    url = settings.REDIS_URL
    if url.startswith("fakeredis://"):
        try:
            import fakeredis.aioredis as fakeredis_async
            return fakeredis_async.FakeRedis()
        except ImportError:
            return None
    from redis.asyncio import Redis
    return Redis.from_url(url, decode_responses=False)


async def create_db_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready.")


async def main() -> None:
    redis = _build_redis()

    # FSM storage
    if redis is not None:
        try:
            fsm_storage = FSMRedisStorage(redis=redis)
        except Exception:
            fsm_storage = MemoryStorage()
    else:
        fsm_storage = MemoryStorage()

    # ── TON Connect manifest server ─────────────────────────────────────────
    if not settings.TON_CONNECT_MANIFEST_URL:
        local_url = await start_manifest_server(port=8080)
        # Patch settings at runtime so wallet handler can read it
        settings.__dict__["TON_CONNECT_MANIFEST_URL"] = local_url
        logger.info(
            "\n"
            "╔══════════════════════════════════════════════════════╗\n"
            "║  📱 Чтобы Tonkeeper подключился с телефона:          ║\n"
            "║  1. Установите ngrok: https://ngrok.com/download     ║\n"
            "║  2. Запустите: ngrok http 8080                       ║\n"
            "║  3. Скопируйте HTTPS-URL из ngrok                    ║\n"
            "║  4. Вставьте в .env:                                 ║\n"
            "║     TON_CONNECT_MANIFEST_URL=https://xxx.ngrok.io/   ║\n"
            "║                    tonconnect-manifest.json          ║\n"
            "╚══════════════════════════════════════════════════════╝"
        )
    else:
        logger.info(f"TON Connect manifest: {settings.TON_CONNECT_MANIFEST_URL}")

    if redis is not None:
        ton_connect_service.init(redis)

    # ── Bot & Dispatcher ────────────────────────────────────────────────────
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=fsm_storage)

    dp.update.outer_middleware(DatabaseMiddleware())
    dp.update.outer_middleware(AuthMiddleware())
    if redis is not None:
        dp.message.middleware(ThrottlingMiddleware(redis=redis, rate_limit=0.5))

    dp.include_router(setup_routers())

    await create_db_tables()

    logger.info("Bot started ✅  Press Ctrl+C to stop.")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        await stop_manifest_server()
        if redis is not None and hasattr(redis, "aclose"):
            await redis.aclose()
        logger.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
