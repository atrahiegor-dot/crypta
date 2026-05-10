"""TON Connect wallet integration service."""
import asyncio
import logging
from io import BytesIO
from typing import Optional

import qrcode
from pytonconnect import TonConnect
from pytonconnect.storage import IStorage

from bot.config import settings

logger = logging.getLogger(__name__)


class RedisStorage(IStorage):
    """Per-user Redis storage for TON Connect session data."""

    def __init__(self, redis_client, user_id: int):
        self._redis = redis_client
        self._prefix = f"tc:{user_id}:"

    async def set_item(self, key: str, value: str):
        await self._redis.set(f"{self._prefix}{key}", value, ex=3600)

    async def get_item(self, key: str, default_value: Optional[str] = None) -> Optional[str]:
        val = await self._redis.get(f"{self._prefix}{key}")
        if val is None:
            return default_value
        return val.decode() if isinstance(val, bytes) else val

    async def remove_item(self, key: str):
        await self._redis.delete(f"{self._prefix}{key}")


class TonConnectService:
    def __init__(self):
        self._connectors: dict[int, TonConnect] = {}
        self._redis = None

    def init(self, redis_client):
        self._redis = redis_client

    def _get_connector(self, user_id: int) -> TonConnect:
        if user_id not in self._connectors:
            storage = RedisStorage(self._redis, user_id)
            self._connectors[user_id] = TonConnect(
                manifest_url=settings.TON_CONNECT_MANIFEST_URL,
                storage=storage,
            )
        return self._connectors[user_id]

    async def generate_connect_url(self, user_id: int) -> tuple[str, list]:
        """Returns (connect_url, wallets_list)."""
        connector = self._get_connector(user_id)
        wallets = await connector.get_wallets()

        # Prefer Tonkeeper, fallback to first available
        wallet = next(
            (w for w in wallets if "tonkeeper" in w.get("name", "").lower()),
            wallets[0] if wallets else None,
        )
        if not wallet:
            raise RuntimeError("No TON wallets available")

        connect_url = await connector.connect(wallet)
        return connect_url, wallets

    async def check_connection(self, user_id: int) -> Optional[str]:
        """Returns wallet address if connected, None otherwise."""
        connector = self._get_connector(user_id)
        try:
            if connector.connected:
                return connector.account.address
        except Exception:
            pass
        return None

    async def wait_for_connection(
        self, user_id: int, timeout: int = 180
    ) -> Optional[str]:
        """Polls for wallet connection. Returns address or None on timeout."""
        connector = self._get_connector(user_id)
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            try:
                if connector.connected:
                    return connector.account.address
            except Exception:
                pass
            await asyncio.sleep(3)
        return None

    async def disconnect(self, user_id: int) -> bool:
        connector = self._get_connector(user_id)
        try:
            await connector.disconnect()
        except Exception:
            pass
        self._connectors.pop(user_id, None)
        return True

    def cleanup_connector(self, user_id: int):
        self._connectors.pop(user_id, None)


def generate_qr_image(data: str) -> BytesIO:
    """Generate QR code PNG image as BytesIO."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    buffer.name = "qr.png"
    return buffer


ton_connect_service = TonConnectService()
