from typing import Optional
from loguru import logger

from models.orator import User
from models.user_settings import UserSettings, UserSettingsUpdate
from services.app_database import app_database_service
from services.security import security_service


class UserService:
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя по username и паролю (не используется в Telegram боте)"""
        try:
            user = await app_database_service.get_user_by_username(username)
            if not user:
                return None

            # Для Telegram бота пароли не используются
            return None
        except Exception as e:
            logger.error(f"User authentication failed: {e}")
            return None

    async def get_or_create_telegram_user(
        self, telegram_id: str, username: str = None, first_name: str = None, last_name: str = None
    ) -> User:
        """Получение или создание пользователя через Telegram"""
        try:
            # Проверяем, существует ли пользователь
            user = await app_database_service.get_user_by_telegram_id(telegram_id)
            if user:
                return user

            # Создаем нового пользователя
            telegram_username = username or f"telegram_{telegram_id}"
            display_name = f"{first_name or ''} {last_name or ''}".strip() or telegram_username

            # Генерируем уникальный username
            base_username = telegram_username
            counter = 1
            while await app_database_service.get_user_by_username(telegram_username):
                telegram_username = f"{base_username}_{counter}"
                counter += 1

            # Создаем пользователя
            telegram_data = {
                "telegram_id": telegram_id,
                "telegram_username": username,
                "first_name": first_name,
                "last_name": last_name,
            }

            user = await app_database_service.create_telegram_user(telegram_data)

            # Создаем настройки по умолчанию
            await self.create_default_settings(str(user.id))

            logger.info(f"New Telegram user created: {user.id}")
            return user

        except Exception as e:
            logger.error(f"Telegram user creation failed: {e}")
            raise

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Получение пользователя по ID"""
        try:
            return await app_database_service.get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"Get user by ID failed: {e}")
            return None

    async def get_user_settings(self, user_id: str) -> Optional[UserSettings]:
        """Получение настроек пользователя"""
        try:
            return await app_database_service.get_user_settings(user_id)
        except Exception as e:
            logger.error(f"Get user settings failed: {e}")
            return None

    async def create_default_settings(self, user_id: str) -> UserSettings:
        """Создание настроек по умолчанию"""
        try:
            default_settings = {
                "language": "ru",
                "show_explanations": True,
                "show_sql": True,
                "max_results": 100,
                "auto_format": True,
            }

            return await app_database_service.create_user_settings(user_id, default_settings)
        except Exception as e:
            logger.error(f"Create default settings failed: {e}")
            raise

    async def update_user_settings(self, user_id: str, settings_update: UserSettingsUpdate) -> UserSettings:
        """Обновление настроек пользователя"""
        try:
            # Фильтруем только непустые значения
            update_data = {}
            for field, value in settings_update.dict().items():
                if value is not None:
                    update_data[field] = value

            return await app_database_service.update_user_settings(user_id, update_data)
        except Exception as e:
            logger.error(f"Update user settings failed: {e}")
            raise

    async def reset_user_settings(self, user_id: str) -> UserSettings:
        """Сброс настроек пользователя к значениям по умолчанию"""
        try:
            # Удаляем текущие настройки
            await app_database_service.delete_user_settings(user_id)

            # Создаем новые настройки по умолчанию
            return await self.create_default_settings(user_id)
        except Exception as e:
            logger.error(f"Reset user settings failed: {e}")
            raise

    async def save_query_history(
        self, user_id: str, natural_query: str, sql_query: str, explanation: str = None, execution_time: float = None
    ):
        """Сохранение истории запросов"""
        try:
            await app_database_service.save_query_history(
                user_id, natural_query, sql_query, explanation, execution_time
            )
        except Exception as e:
            logger.error(f"Save query history failed: {e}")


# Создание экземпляра сервиса
user_service = UserService()
