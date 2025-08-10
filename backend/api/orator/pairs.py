from models.orator.message_queue import MessageQueue
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

        # Добавляем сообщение в очередь с кнопками
        user_profile = await orator_db.get_user_profile(current_user_id)
        candidate_profile = await orator_db.get_user_profile(candidate_id)
        if user_profile["username"] == "":
            username = ""
        else:
            username = f" {user_profile['username']}"

        # Создаем клавиатуру с кнопками подтверждения/отмены
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Подтвердить", "callback_data": f"pair_confirm_{user_pair['id']}"},
                    {"text": "❌ Отменить", "callback_data": f"pair_cancel_{user_pair['id']}"},
                ]
            ]
        }

        message_queue = MessageQueue(
            user_id=candidate_profile["telegram_id"],
            message=f"Вы были добавлены в пару с кандидатом {user_profile['first_name']} @{username}",
            keyboard=keyboard,
        )
        await orator_db.add_message(message_queue)

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

        # Добавляем сообщение в очередь
        user_profile = await orator_db.get_user_profile(current_user_id)
        candidate_id = user_pair["user2_id"]
        candidate_profile = await orator_db.get_user_profile(candidate_id)
        if candidate_profile["username"] == "":
            username = ""
        else:
            username = f" {candidate_profile['username']}"

        message_queue = MessageQueue(
            user_id=candidate_profile["telegram_id"],
            message=f"Пара с {user_profile['first_name']} @{username} подтверждена. Начинайте тренировку!",
        )
        await orator_db.add_message(message_queue)

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


@router.post("/{pair_id}/cancel", response_model=UserPairResponse)
async def cancel_pair(pair_id: str, current_user_id: str = Depends(security_service.get_current_user_id)):
    """Отменить пару"""
    try:
        user_pair = await orator_db.cancel_user_pair(pair_id, current_user_id)
        if not user_pair:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Pair not found or you don't have permission to cancel it"
            )

        # Добавляем сообщение в очередь только если пара была действительно отменена (не была отменена ранее)
        # Проверяем, что cancelled_at не NULL (пара была только что отменена)
        if user_pair.get("cancelled_at") is not None:
            user_profile = await orator_db.get_user_profile(current_user_id)
            if user_pair["user2_id"] == current_user_id:
                candidate_id = user_pair["user1_id"]
            else:
                candidate_id = user_pair["user2_id"]
            candidate_profile = await orator_db.get_user_profile(candidate_id)
            if candidate_profile["username"] == "":
                username = ""
            else:
                username = f" {candidate_profile['username']}"
            message_queue = MessageQueue(
                user_id=candidate_profile["telegram_id"],
                message=f"Пара с {user_profile['first_name']} @{username} отменена. Попробуйте найти другую пару.",
            )
            await orator_db.add_message(message_queue)

        return UserPairResponse.from_user_pair(user_pair)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel pair error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to cancel pair")
