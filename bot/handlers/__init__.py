from aiogram import Router

from bot.handlers import start, profile, tasks, wallet, leaderboard, referral, checkin, moderation, admin

def setup_routers() -> Router:
    root = Router()
    root.include_router(start.router)
    root.include_router(profile.router)
    root.include_router(tasks.router)
    root.include_router(wallet.router)
    root.include_router(leaderboard.router)
    root.include_router(referral.router)
    root.include_router(checkin.router)
    root.include_router(moderation.router)
    root.include_router(admin.router)
    return root
