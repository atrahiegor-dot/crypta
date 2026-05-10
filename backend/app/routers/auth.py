from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from ..config import settings
from ..database import async_session_maker
from ..schemas import AuthRequest, AuthResponse
from ..security import create_access_token, validate_telegram_init_data

from bot.database.models import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=AuthResponse)
async def auth_telegram(body: AuthRequest):
    """Validate Telegram WebApp initData and issue a JWT."""
    if settings.BOT_TOKEN:
        try:
            data = validate_telegram_init_data(body.init_data)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
        tg_user = data["user"]
    else:
        import json, urllib.parse
        from urllib.parse import parse_qsl
        parsed = dict(parse_qsl(body.init_data, keep_blank_values=True))
        raw = parsed.get("user", '{"id":1,"first_name":"Dev","username":"dev"}')
        tg_user = json.loads(urllib.parse.unquote(raw))

    telegram_id = int(tg_user.get("id", 0))
    if not telegram_id:
        raise HTTPException(status_code=400, detail="Invalid user data")

    async with async_session_maker() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            role = UserRole.DEVELOPER if telegram_id in settings.ADMIN_IDS else UserRole.USER
            user = User(
                telegram_id=telegram_id,
                first_name=tg_user.get("first_name", "User"),
                last_name=tg_user.get("last_name"),
                username=tg_user.get("username"),
                role=role,
            )
            session.add(user)
            await session.flush()
        else:
            user.first_name = tg_user.get("first_name", user.first_name)
            if tg_user.get("last_name") is not None:
                user.last_name = tg_user.get("last_name")
            if tg_user.get("username") is not None:
                user.username = tg_user.get("username")

        await session.commit()
        await session.refresh(user)

        token = create_access_token(telegram_id=user.telegram_id, user_db_id=user.id)
        return AuthResponse(access_token=token)
