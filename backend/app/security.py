import hmac
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.parse import parse_qsl, unquote

from jose import JWTError, jwt

from .config import settings


# ─── Telegram initData validation ────────────────────────────────────────────


def validate_telegram_init_data(init_data: str) -> dict:
    """
    Validate Telegram WebApp initData and return parsed data.
    Raises ValueError on invalid signature.
    """
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    hash_value = parsed.pop("hash", None)

    if not hash_value:
        raise ValueError("No hash in init_data")

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    secret_key = hmac.digest(
        b"WebAppData",
        settings.BOT_TOKEN.encode(),
        "sha256",
    )
    computed = hmac.digest(
        secret_key,
        data_check_string.encode(),
        "sha256",
    ).hex()

    if not hmac.compare_digest(computed, hash_value):
        raise ValueError("Invalid Telegram signature")

    # Parse nested user JSON
    raw_user = parsed.get("user", "{}")
    try:
        user = json.loads(unquote(raw_user))
    except json.JSONDecodeError:
        user = {}

    return {
        "user": user,
        "auth_date": int(parsed.get("auth_date", 0)),
        "query_id": parsed.get("query_id"),
    }


# ─── JWT ─────────────────────────────────────────────────────────────────────


def create_access_token(telegram_id: int, user_db_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {
        "sub": str(telegram_id),
        "uid": user_db_id,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        return None
