import sys
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings

# Project root: монета/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Make bot importable from backend
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    DATABASE_URL: str = ""
    REDIS_URL: str = "fakeredis://"
    ADMIN_IDS: List[int] = []

    # JWT
    JWT_SECRET: str = "tasker-mini-app-jwt-secret-change-in-prod"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 168  # 7 days

    # Uploads
    UPLOAD_DIR: str = str(PROJECT_ROOT / "uploads")
    MAX_UPLOAD_SIZE_MB: int = 50

    # XP
    WALLET_CONNECT_XP: int = 500
    REFERRAL_XP: int = 100
    DAILY_CHECKIN_BASE_XP: int = 50

    class Config:
        env_file = str(PROJECT_ROOT / ".env")
        extra = "ignore"

    @property
    def db_url(self) -> str:
        """Resolve relative SQLite path to absolute."""
        url = self.DATABASE_URL
        if not url:
            return f"sqlite+aiosqlite:///{PROJECT_ROOT / 'tonbot.db'}"
        if "sqlite" in url and ":///./" in url:
            rel = url.split(":///./", 1)[1]
            abs_path = PROJECT_ROOT / rel
            return f"sqlite+aiosqlite:///{abs_path}"
        return url


settings = Settings()
