"""
Обработчик событий подписки/отписки от каналов
"""

import asyncio
from telegram import Update, ChatMemberUpdated, ChatMember
from telegram.ext import ContextTypes, ChatMemberHandler
from loguru import logger

from .base_handler import OratorBaseHandler


class ChatMemberHandler(OratorBaseHandler):
    """Обработчик событий подписки/отписки от каналов"""

    def __init__(self, api_client, content_manager):
        super().__init__(api_client, content_manager)

    async def handle_chat_member_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработка обновлений статуса участника чата"""
        try:
            # Получаем информацию об обновлении
            chat_member_update: ChatMemberUpdated = update.chat_member

            # Информация о чате и пользователе
            chat = chat_member_update.chat
            user = chat_member_update.new_chat_member.user
            old_status = chat_member_update.old_chat_member.status
            new_status = chat_member_update.new_chat_member.status

            logger.info(
                f"Chat member update: user {user.id} in chat {chat.id} "
                f"status changed from {old_status} to {new_status}"
            )

            # Определяем действие
            if new_status in ["member", "administrator", "creator"]:
                # Пользователь присоединился к каналу
                await self._handle_user_joined(chat.id, user, new_status)
            elif old_status in ["member", "administrator", "creator"] and new_status in ["left", "kicked"]:
                # Пользователь покинул канал
                await self._handle_user_left(chat.id, user, new_status)

        except Exception as e:
            logger.error(f"Error handling chat member update: {e}")

    async def _handle_user_joined(self, chat_id: int, user, status: str) -> None:
        """Обработка присоединения пользователя к каналу"""
        try:
            # Сохраняем информацию о подписчике в базу данных
            await self._save_subscriber(chat_id, user.id, status)
            logger.info(f"User {user.id} joined channel {chat_id} with status {status}")

        except Exception as e:
            logger.error(f"Error handling user join: {e}")

    async def _handle_user_left(self, chat_id: int, user, status: str) -> None:
        """Обработка выхода пользователя из канала"""
        try:
            # Обновляем статус подписчика в базе данных
            await self._save_subscriber(chat_id, user.id, status)
            logger.info(f"User {user.id} left channel {chat_id} with status {status}")

        except Exception as e:
            logger.error(f"Error handling user leave: {e}")

    async def _save_subscriber(self, chat_id: int, user_id: int, status: str) -> None:
        """Сохранение/обновление информации о подписчике в базе данных"""
        try:
            # Вызываем API для сохранения подписчика
            response = await self.api_client.post(
                "/api/v1/channels/save_subscriber", json={"chat_id": chat_id, "user_id": user_id, "status": status}
            )

            logger.info(f"Successfully saved subscriber: chat_id={chat_id}, user_id={user_id}, status={status}")

        except Exception as e:
            logger.error(f"Error saving subscriber: {e}")
