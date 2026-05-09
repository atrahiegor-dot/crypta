"""
Embedded HTTP server that serves tonconnect-manifest.json locally.
For public access use ngrok: ngrok http 8080
Then set TON_CONNECT_MANIFEST_URL=https://<ngrok-url>/tonconnect-manifest.json
"""
import json
import asyncio
import socket
import logging
from pathlib import Path
from aiohttp import web

logger = logging.getLogger(__name__)

MANIFEST_PATH = Path(__file__).parent.parent.parent / "tonconnect-manifest.json"
_runner: web.AppRunner | None = None


def _get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


async def _handle_manifest(request: web.Request) -> web.Response:
    if not MANIFEST_PATH.exists():
        return web.Response(status=404, text="manifest not found")
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return web.Response(
        content_type="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
        text=json.dumps(data),
    )


async def _handle_health(request: web.Request) -> web.Response:
    return web.Response(text="ok")


async def start_manifest_server(port: int = 8080) -> str:
    """
    Start the manifest server and return the local URL.
    If TON_CONNECT_MANIFEST_URL is already set in .env, skip.
    """
    global _runner

    app = web.Application()
    app.router.add_get("/tonconnect-manifest.json", _handle_manifest)
    app.router.add_get("/health", _handle_health)

    _runner = web.AppRunner(app)
    await _runner.setup()
    site = web.TCPSite(_runner, "0.0.0.0", port)
    await site.start()

    local_ip = _get_local_ip()
    local_url = f"http://{local_ip}:{port}/tonconnect-manifest.json"
    logger.info(f"Manifest server started → {local_url}")
    logger.info(
        "For Tonkeeper to reach the manifest from a phone, expose via ngrok:\n"
        f"  ngrok http {port}\n"
        "Then set TON_CONNECT_MANIFEST_URL=https://<ngrok-id>.ngrok.io/tonconnect-manifest.json"
    )
    return local_url


async def stop_manifest_server() -> None:
    global _runner
    if _runner:
        await _runner.cleanup()
        _runner = None
