from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram
    BOT_TOKEN: str
    BOT_USERNAME: str = ""

    # Database (default: local SQLite for dev; change to postgresql+asyncpg://... for prod)
    DATABASE_URL: str = "sqlite+aiosqlite:///./tonbot.db"

    # Redis (default: fakeredis for dev; change to redis://localhost:6379/0 for prod)
    REDIS_URL: str = "fakeredis://"

    # TON Connect
    TON_CONNECT_MANIFEST_URL: str = ""

    # Admins (developer role)
    ADMIN_IDS: List[int] = Field(default_factory=list)

    # XP rewards
    WALLET_CONNECT_XP: int = 500
    REFERRAL_XP: int = 100
    DAILY_CHECKIN_BASE_XP: int = 50

    # Mini App
    MINI_APP_URL: str = ""

    # Webhook (optional)
    WEBHOOK_ENABLED: bool = False
    WEBHOOK_URL: str = ""
    WEBHOOK_PORT: int = 8080


settings = Settings()
