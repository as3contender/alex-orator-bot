from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger

from models.orator import UserProfile, UserProfileUpdate, UserStats
from services.security import security_service
from services.orator_database import orator_db

router = APIRouter()


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user_id: str = Depends(security_service.get_current_user_id)):
    """Получить профиль текущего пользователя"""
    try:
        profile = await orator_db.get_user_profile(current_user_id)
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        return profile
    except Exception as e:
        logger.error(f"Get profile error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get profile")


@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    profile_update: UserProfileUpdate, current_user_id: str = Depends(security_service.get_current_user_id)
):
    """Обновить профиль пользователя"""
    try:
        profile = await orator_db.update_user_profile(current_user_id, profile_update)
        return profile
    except Exception as e:
        logger.error(f"Update profile error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update profile")


@router.get("/stats", response_model=UserStats)
async def get_user_stats(current_user_id: str = Depends(security_service.get_current_user_id)):
    """Получить статистику пользователя"""
    try:
        stats = await orator_db.get_user_stats(current_user_id)
        return stats
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get stats")
