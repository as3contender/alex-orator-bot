from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from loguru import logger

from models.auth import UserLogin, UserCreate
from models.orator import UserResponse, TokenResponse
from models.telegram import TelegramAuth
from services.security import security_service
from services.user_service import user_service

router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Стандартная аутентификация по email/username и паролю"""
    try:
        user = await user_service.authenticate_user(user_data.username, user_data.password)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

        token = security_service.create_access_token(data={"sub": str(user.id)})
        logger.info(f"User logged in: {user.id}")

        return TokenResponse(access_token=token, token_type="bearer", user=UserResponse.from_user(user))
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authentication failed")


@router.post("/telegram", response_model=TokenResponse)
async def telegram_auth(telegram_data: TelegramAuth):
    """Аутентификация через Telegram"""
    try:
        user = await user_service.get_or_create_telegram_user(
            telegram_id=telegram_data.telegram_id,
            username=telegram_data.telegram_username,
            first_name=telegram_data.first_name,
            last_name=telegram_data.last_name,
        )

        token = security_service.create_access_token(data={"sub": str(user.id)})
        logger.info(f"Telegram user authenticated: {user.id}")

        return TokenResponse(access_token=token, token_type="bearer", user=UserResponse.from_user(user))
    except Exception as e:
        logger.error(f"Telegram auth error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Telegram authentication failed")


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Регистрация нового пользователя"""
    try:
        user = await user_service.create_user(user_data)
        logger.info(f"New user registered: {user.id}")
        return UserResponse.from_user(user)
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration failed")


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user_id: str = Depends(security_service.get_current_user_id)):
    """Получение информации о текущем пользователе"""
    try:
        user = await user_service.get_user_by_id(current_user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return UserResponse.from_user(user)
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user info")
