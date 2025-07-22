from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from typing import List

from models.orator import OratorSettings, OratorSettingsUpdate
from services.security import security_service
from services.orator_database import orator_db

router = APIRouter()


@router.get("/", response_model=List[OratorSettings])
async def get_all_settings(current_user_id: str = Depends(security_service.get_current_user_id)):
    """Получить все настройки бота (только для админов)"""
    try:
        # TODO: Добавить проверку на админа
        settings = await orator_db.get_all_settings()
        return settings
    except Exception as e:
        logger.error(f"Get settings error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get settings")


@router.put("/{key}", response_model=OratorSettings)
async def update_setting(
    key: str, setting_update: OratorSettingsUpdate, current_user_id: str = Depends(security_service.get_current_user_id)
):
    """Обновить настройку бота (только для админов)"""
    try:
        # TODO: Добавить проверку на админа
        setting = await orator_db.update_setting(key, setting_update.value, setting_update.description)
        return setting
    except Exception as e:
        logger.error(f"Update setting error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update setting")
