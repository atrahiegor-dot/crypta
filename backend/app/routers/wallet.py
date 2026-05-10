from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from ..config import settings
from ..deps import CurrentUserDep, SessionDep
from ..schemas import MessageResponse, WalletConnectRequest, WalletStatus
from bot.database.models import AchievementType, Achievement, User

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("/status", response_model=WalletStatus)
async def wallet_status(session: SessionDep, current: CurrentUserDep):
    result = await session.execute(select(User).where(User.id == current["user_id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return WalletStatus(
        connected=bool(user.wallet_address),
        address=user.wallet_address,
        connected_at=user.wallet_connected_at,
    )


@router.post("/connect", response_model=MessageResponse)
async def connect_wallet(
    body: WalletConnectRequest,
    session: SessionDep,
    current: CurrentUserDep,
):
    result = await session.execute(select(User).where(User.id == current["user_id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    already_had = bool(user.wallet_address)
    user.wallet_address = body.wallet_address
    user.wallet_connected_at = datetime.now(timezone.utc)

    xp_awarded = 0
    if not already_had:
        user.xp_points += settings.WALLET_CONNECT_XP
        xp_awarded = settings.WALLET_CONNECT_XP

        # Grant achievement
        ach_res = await session.execute(
            select(Achievement).where(
                Achievement.user_id == user.id,
                Achievement.achievement_type == AchievementType.WALLET_CONNECTED,
            )
        )
        if not ach_res.scalar_one_or_none():
            session.add(
                Achievement(
                    user_id=user.id,
                    achievement_type=AchievementType.WALLET_CONNECTED,
                )
            )

    await session.commit()
    return MessageResponse(
        message=f"Wallet connected! +{xp_awarded} XP" if xp_awarded else "Wallet updated.",
        xp_awarded=xp_awarded or None,
    )


@router.delete("/disconnect", response_model=MessageResponse)
async def disconnect_wallet(session: SessionDep, current: CurrentUserDep):
    result = await session.execute(select(User).where(User.id == current["user_id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.wallet_address = None
    user.wallet_connected_at = None
    await session.commit()
    return MessageResponse(message="Wallet disconnected.")
