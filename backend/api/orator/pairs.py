from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from typing import List

from models.orator import UserPairResponse
from services.security import security_service
from services.orator_database import orator_db

router = APIRouter()


@router.post("/create", response_model=UserPairResponse)
async def create_pair(
    pair_data: dict, current_user_id: str = Depends(security_service.get_current_user_id)  # {"candidate_id": "uuid"}
):
    """Создать пару с кандидатом"""
    try:
        candidate_id = pair_data.get("candidate_id")
        if not candidate_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="candidate_id is required")

        # Получаем текущую регистрацию пользователя
        registration = await orator_db.get_user_week_registration(current_user_id)
        if not registration:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active registration found")

        user_pair = await orator_db.create_user_pair(
            user1_id=current_user_id, user2_id=candidate_id, registration_id=registration["id"]
        )

        if not user_pair:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create pair")

        return UserPairResponse.from_user_pair(user_pair)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create pair error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create pair")


@router.post("/{pair_id}/confirm", response_model=UserPairResponse)
async def confirm_pair(pair_id: str, current_user_id: str = Depends(security_service.get_current_user_id)):
    """Подтвердить пару"""
    try:
        user_pair = await orator_db.confirm_user_pair(pair_id, True)
        if not user_pair:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pair not found")

        return UserPairResponse.from_user_pair(user_pair)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Confirm pair error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to confirm pair")


@router.get("/", response_model=List[UserPairResponse])
async def get_user_pairs(current_user_id: str = Depends(security_service.get_current_user_id)):
    """Получить все пары пользователя"""
    try:
        # Получаем текущую регистрацию
        registration = await orator_db.get_user_week_registration(current_user_id)
        if not registration:
            return []

        pairs = await orator_db.get_user_pairs(current_user_id, registration["week_start_date"])
        return [UserPairResponse.from_user_pair(pair) for pair in pairs]
    except Exception as e:
        logger.error(f"Get user pairs error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user pairs")
