"""
API для обработки подписчиков каналов
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from loguru import logger

from services.channel_subscriber_service import channel_subscriber_service

router = APIRouter()


class ChannelSubscriberRequest(BaseModel):
    chat_id: int
    user_id: int
    status: str  # "member", "left", "kicked", "administrator", "creator"


@router.post("/save_subscriber")
async def save_channel_subscriber(request: ChannelSubscriberRequest):
    """Сохранение/обновление информации о подписчике канала"""
    try:
        success = await channel_subscriber_service.save_subscriber(request.chat_id, request.user_id, request.status)

        if success:
            return {"success": True, "message": "Subscriber saved successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save subscriber")

    except Exception as e:
        logger.error(f"Error saving channel subscriber: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/subscribers/{chat_id}")
async def get_channel_subscribers(chat_id: int):
    """Получение списка подписчиков канала"""
    try:
        subscribers = await channel_subscriber_service.get_channel_subscribers(chat_id)
        return {"chat_id": chat_id, "subscribers": subscribers}

    except Exception as e:
        logger.error(f"Error getting channel subscribers: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/user_channels/{user_id}")
async def get_user_channels(user_id: int):
    """Получение списка каналов пользователя"""
    try:
        channels = await channel_subscriber_service.get_user_channels(user_id)
        return {"user_id": user_id, "channels": channels}

    except Exception as e:
        logger.error(f"Error getting user channels: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
