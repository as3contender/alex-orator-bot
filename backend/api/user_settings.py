from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from typing import List

from models.user_settings import UserSettings, UserSettingsUpdate
from services.user_service import user_service
from services.security import security_service

router = APIRouter()


@router.get("/", response_model=UserSettings)
async def get_user_settings(current_user_id: str = Depends(security_service.get_current_user_id)):
    """Получение настроек пользователя"""
    try:
        settings = await user_service.get_user_settings(current_user_id)
        if not settings:
            # Создаем настройки по умолчанию
            settings = await user_service.create_default_settings(current_user_id)

        return settings
    except Exception as e:
        logger.error(f"Get user settings error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user settings")


@router.put("/", response_model=UserSettings)
async def update_user_settings(
    settings_update: UserSettingsUpdate, current_user_id: str = Depends(security_service.get_current_user_id)
):
    """Обновление настроек пользователя"""
    try:
        updated_settings = await user_service.update_user_settings(
            user_id=current_user_id, settings_update=settings_update
        )
        logger.info(f"User {current_user_id} updated settings")
        return updated_settings
    except Exception as e:
        logger.error(f"Update user settings error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update user settings")


@router.post("/reset")
async def reset_user_settings(current_user_id: str = Depends(security_service.get_current_user_id)):
    """Сброс настроек пользователя к значениям по умолчанию"""
    try:
        await user_service.reset_user_settings(current_user_id)
        logger.info(f"User {current_user_id} reset settings to default")
        return {"message": "Settings reset to default"}
    except Exception as e:
        logger.error(f"Reset user settings error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reset user settings")
