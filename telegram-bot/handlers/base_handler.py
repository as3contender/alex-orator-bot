"""
Базовый класс для всех обработчиков
"""

from telegram import Update
from loguru import logger

from orator_api_client import OratorAPIClient
from orator_translations import get_text


def format_text_for_telegram(text: str) -> str:
    """Форматирует текст для корректного отображения в Telegram HTML режиме"""
    if not text:
        return text

    # Заменяем переносы строк на HTML переносы
    # Двойные переносы \n\n становятся <br><br> для абзацев
    # Одинарные переносы \n становятся <br> для строк
    formatted_text = text.replace("\n\n", "<br><br>").replace("\n", "<br>")

    return formatted_text


class OratorBaseHandler:
    """Базовый класс для всех обработчиков"""

    def __init__(self, api_client: OratorAPIClient, content_manager=None):
        self.api_client = api_client
        self.content_manager = content_manager

    def _format_text_for_telegram(self, text: str) -> str:
        """Форматирует текст для корректного отображения в Telegram HTML режиме"""
        return format_text_for_telegram(text)

    async def _authenticate_user(self, update: Update) -> bool:
        """Аутентификация пользователя через Telegram"""
        try:
            user = update.effective_user
            await self.api_client.authenticate_telegram_user(
                telegram_id=str(user.id), username=user.username, first_name=user.first_name, last_name=user.last_name
            )
            return True
        except Exception as e:
            logger.error(f"Authentication failed for user {user.id}: {e}")
            return False

    async def _get_user_language(self, update: Update) -> str:
        """Получение языка пользователя"""
        try:
            settings = await self.api_client.get_user_settings()
            return settings.get("language", "ru")
        except:
            return "ru"

    async def _get_bot_content(self, content_key: str, language: str = "ru") -> str:
        """Получить контент бота из кэша или базы данных"""
        if self.content_manager and self.content_manager.is_content_loaded():
            # Контент уже отформатирован в content_manager
            return self.content_manager.get_content(content_key, language)

        # Fallback к API запросу
        try:
            response = await self.api_client.get_bot_content(content_key)
            content = response.get("content_text", f"Контент не найден: {content_key}")
            # Форматируем только при fallback
            return self._format_text_for_telegram(content)
        except Exception as e:
            logger.error(f"Error getting bot content for key '{content_key}': {e}")
            # Возвращаем fallback текст
            return get_text(content_key, language)

    async def _get_exercise_by_topic(self, topic_id: str, language: str = "ru") -> str:
        """Получить упражнение по теме из кэша или базы данных"""
        if self.content_manager and self.content_manager.is_content_loaded():
            # Контент уже отформатирован в content_manager
            return self.content_manager.get_exercise(topic_id, language)

        # Fallback к API запросу
        try:
            response = await self.api_client.get_bot_content(f"exercise_{topic_id}")
            content = response.get("content_text", f"Упражнение не найдено для темы: {topic_id}")
            # Форматируем только при fallback
            return self._format_text_for_telegram(content)
        except Exception as e:
            logger.error(f"Error getting exercise for topic '{topic_id}': {e}")
            return f"Упражнение для темы '{topic_id}' не найдено"

    def _find_topic_name(self, topic_tree: dict, topic_id: str) -> str:
        """Найти название темы по ID в дереве тем"""

        def search_in_topics(topics):
            for topic in topics:
                if topic["id"] == topic_id:
                    return topic["name"]
                # Рекурсивно ищем в дочерних темах
                if "children" in topic:
                    result = search_in_topics(topic["children"])
                    if result:
                        return result
            return None

        return search_in_topics(topic_tree.get("topics", []))
