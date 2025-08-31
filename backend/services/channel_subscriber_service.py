"""
Сервис для работы с подписчиками каналов
"""

from typing import List, Dict, Any
from loguru import logger

from services.app_database import app_database_service


class ChannelSubscriberService:
    async def save_subscriber(self, chat_id: int, user_id: int, status: str) -> bool:
        """Сохранение/обновление информации о подписчике канала"""
        try:
            async with app_database_service.pool.acquire() as conn:
                # Используем UPSERT для обновления существующей записи или создания новой
                await conn.execute(
                    """
                    INSERT INTO channel_subscribers (chat_id, user_id, status, updated_at)
                    VALUES ($1, $2, $3, NOW())
                    ON CONFLICT (chat_id, user_id)
                    DO UPDATE SET 
                        status = EXCLUDED.status,
                        updated_at = NOW()
                    """,
                    chat_id,
                    user_id,
                    status,
                )

            logger.info(f"Saved channel subscriber: chat_id={chat_id}, user_id={user_id}, status={status}")
            return True

        except Exception as e:
            logger.error(f"Error saving channel subscriber: {e}")
            return False

    async def get_channel_subscribers(self, chat_id: int) -> List[Dict[str, Any]]:
        """Получение списка подписчиков канала"""
        try:
            async with app_database_service.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT user_id, status, created_at, updated_at
                    FROM channel_subscribers
                    WHERE chat_id = $1
                    ORDER BY updated_at DESC
                    """,
                    chat_id,
                )

            subscribers = [
                {
                    "user_id": row["user_id"],
                    "status": row["status"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                }
                for row in rows
            ]

            return subscribers

        except Exception as e:
            logger.error(f"Error getting channel subscribers: {e}")
            return []

    async def get_user_channels(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение списка каналов пользователя"""
        try:
            async with app_database_service.pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT chat_id, status, created_at, updated_at
                    FROM channel_subscribers
                    WHERE user_id = $1
                    ORDER BY updated_at DESC
                    """,
                    user_id,
                )

            channels = [
                {
                    "chat_id": row["chat_id"],
                    "status": row["status"],
                    "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                    "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
                }
                for row in rows
            ]

            return channels

        except Exception as e:
            logger.error(f"Error getting user channels: {e}")
            return []

    async def get_active_subscribers_count(self, chat_id: int) -> int:
        """Получение количества активных подписчиков канала"""
        try:
            async with app_database_service.pool.acquire() as conn:
                count = await conn.fetchval(
                    """
                    SELECT COUNT(*)
                    FROM channel_subscribers
                    WHERE chat_id = $1 AND status IN ('member', 'administrator', 'creator')
                    """,
                    chat_id,
                )

            return count or 0

        except Exception as e:
            logger.error(f"Error getting active subscribers count: {e}")
            return 0


# Создаем глобальный экземпляр сервиса
channel_subscriber_service = ChannelSubscriberService()
