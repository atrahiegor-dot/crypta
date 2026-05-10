"""FastAPI backend for Tasker Mini App."""
import sys
import os
from pathlib import Path

# ── MUST be first: add project root to path & load .env ──────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env so bot.config (which uses env_file=".env") finds its variables
_env_path = PROJECT_ROOT / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(str(_env_path), override=False)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .routers import auth, leaderboard, moderation, profile, tasks, wallet

app = FastAPI(
    title="Tasker API",
    version="1.0.0",
    description="Backend API for Tasker Telegram Mini App",
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static files (uploaded proofs) ───────────────────────────────────────────
uploads_dir = Path(settings.UPLOAD_DIR)
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(tasks.router)
app.include_router(leaderboard.router)
app.include_router(wallet.router)
app.include_router(moderation.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "tasker-api"}
