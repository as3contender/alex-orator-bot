from models.orator.message_queue import MessageQueue
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from typing import List

from models.orator import UserPairResponse
from services.security import security_service
from services.orator_database import orator_db
from urllib.parse import quote

router = APIRouter()


def escape_html(text: str) -> str:
    """Экранирует HTML символы"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


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
        partner_profile = await orator_db.get_user_profile(candidate_id)

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
            user_id=partner_profile["telegram_id"],
            message=f"Вы были добавлены в пару с кандидатом {user_profile['first_name']}",
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
        user_pair = await orator_db.confirm_user_pair(pair_id, True, current_user_id)
        if not user_pair:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pair not found")

        # Добавляем сообщение о подтверждении партнеру в очередь
        user_profile = await orator_db.get_user_profile(current_user_id)
        partner_profile = await orator_db.get_user_profile(user_pair["partner_id"])

        if user_profile["username"] is None or user_profile["username"] == "":
            user_link = (
                f'<a href="tg://user?id={user_profile["telegram_id"]}">{escape_html(user_profile["first_name"])}</a>'
            )
        else:
            user_link = f"@{user_profile['username']}"

        message_queue = MessageQueue(
            user_id=partner_profile["telegram_id"],
            message=f"Пара с {user_profile['first_name']} {user_link} подтверждена. Начинайте тренировку!",
        )
        await orator_db.add_message(message_queue)

        # Добавить сообщение с ником и кнопкой написать в телеграм

        message_text = "Привет! Я от @AlexOratorBot"
        start_dialog_message = quote(message_text)

        if partner_profile["username"] is None or partner_profile["username"] == "":
            keyboard = {
                "inline_keyboard": [
                    [
                        {
                            "text": "✉️ Написать в Telegram",
                            "url": f"tg://user?id={partner_profile['telegram_id']}&text={start_dialog_message}",
                        },
                    ]
                ]
            }
        else:
            keyboard = {
                "inline_keyboard": [
                    [
                        {
                            "text": "✉️ Написать в Telegram",
                            "url": f"https://t.me/{partner_profile['username']}?text={start_dialog_message}",
                        },
                    ]
                ]
            }

        if partner_profile["username"] is None or partner_profile["username"] == "":
            user_link = f'<a href="tg://user?id={partner_profile["telegram_id"]}">{escape_html(partner_profile["first_name"])}</a>'
        else:
            user_link = f"@{partner_profile['username']}"

        message_queue = MessageQueue(
            user_id=user_profile["telegram_id"],
            message=f"Вы подтвердили пару с {partner_profile['first_name']} {user_link}. Начинайте тренировку!",
            keyboard=keyboard,
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
            partner_profile = await orator_db.get_user_profile(user_pair["partner_id"])
            message_queue = MessageQueue(
                user_id=partner_profile["telegram_id"],
                message=f"Пара с {user_profile['first_name']} отменена. Попробуйте найти другую пару.",
            )
            await orator_db.add_message(message_queue)

        return UserPairResponse.from_user_pair(user_pair)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel pair error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to cancel pair")
