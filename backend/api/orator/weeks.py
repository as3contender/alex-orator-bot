from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from typing import Optional

from models.orator import WeekRegistrationCreate, WeekRegistrationResponse, WeekInfo
from services.security import security_service
from services.orator_database import orator_db

router = APIRouter()


@router.post("/register", response_model=WeekRegistrationResponse)
async def register_for_week(
    registration: WeekRegistrationCreate, current_user_id: str = Depends(security_service.get_current_user_id)
):
    """Зарегистрироваться на неделю"""
    try:
        # Проверяем, может ли пользователь регистрироваться
        can_register = await orator_db.can_user_register_again(current_user_id)
        if not can_register:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot register again. Please provide feedback for previous sessions first.",
            )

        # Получаем информацию о неделе на основе типа
        week_info = await orator_db.get_week_info(registration.week_type.value)

        week_registration = await orator_db.create_week_registration(
            user_id=current_user_id,
            week_start=week_info["week_start_date"],
            week_end=week_info["week_end_date"],
            preferred_time=registration.preferred_time_msk,
            selected_topics=registration.selected_topics,
        )

        if not week_registration:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create registration"
            )

        return WeekRegistrationResponse.from_week_registration(week_registration)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Register for week error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to register for week")


@router.get("/current", response_model=Optional[WeekRegistrationResponse])
async def get_current_week_registration(current_user_id: str = Depends(security_service.get_current_user_id)):
    """Получить текущую регистрацию на неделю"""
    try:
        registration = await orator_db.get_user_week_registration(current_user_id)
        if registration:
            return WeekRegistrationResponse.from_week_registration(registration)
        return None
    except Exception as e:
        logger.error(f"Get current week registration error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get week registration")


@router.delete("/cancel")
async def cancel_week_registration(current_user_id: str = Depends(security_service.get_current_user_id)):
    """Отменить регистрацию на неделю"""
    try:
        # Получаем текущую регистрацию
        registration = await orator_db.get_user_week_registration(current_user_id)
        if not registration:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active registration found")

        success = await orator_db.cancel_week_registration(current_user_id, registration["week_start_date"])
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active registration found")
        return {"message": "Registration cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel week registration error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to cancel registration")


@router.get("/info", response_model=WeekInfo)
async def get_week_info():
    """Получить информацию о текущей неделе"""
    try:
        week_info = await orator_db.get_week_info("current")
        return week_info
    except Exception as e:
        logger.error(f"Get week info error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get week info")
