"""
Менеджер контента бота - загружает и кэширует сообщения из базы данных
"""

from typing import Dict, Optional
from loguru import logger
from orator_api_client import OratorAPIClient


def format_text_for_telegram(text: str) -> str:
    """Форматирует текст для корректного отображения в Telegram"""
    if not text:
        return text

    # Заменяем HTML теги на обычные переносы строк
    # Убираем <br/> и <br> теги, заменяя на \n
    formatted_text = text.replace("<br/>", "\n").replace("<br>", "\n")

    return formatted_text


class BotContentManager:
    def __init__(self, api_client: OratorAPIClient):
        self.api_client = api_client
        self.content_cache: Dict[str, Dict[str, str]] = {}  # {language: {key: text}}
        self.is_loaded = False

    async def load_content(self, languages: list = None):
        """
        Загрузить весь контент бота в кэш

        Args:
            languages: Список языков для загрузки (по умолчанию ['ru'])
        """
        if languages is None:
            languages = ["ru"]

        logger.info(f"Loading bot content for languages: {languages}")

        try:
            # Список ключей контента для загрузки
            content_keys = [
                "welcome_message",
                "хочешь_тренироваться_на_этой_неделе_второе_сообщение",
                "обратная_связь_для_регистрации_на_следующую_неделю",
                "chat_rules",
                "help_message",
            ]

            # Добавляем упражнения (они загружаются по мере необходимости)
            # Упражнения имеют ключи вида: exercise_[тема]_[уровень]_[задание]

            # Загружаем контент для каждого языка
            for language in languages:
                self.content_cache[language] = {}

                for key in content_keys:
                    try:
                        response = await self.api_client.get_bot_content(key)
                        content_text = response.get("content_text", "")

                        if content_text:
                            # Форматируем текст для Telegram при загрузке
                            formatted_text = format_text_for_telegram(content_text)
                            self.content_cache[language][key] = formatted_text
                            logger.info(f"Loaded and formatted content for key '{key}' in language '{language}'")
                        else:
                            logger.warning(f"No content found for key '{key}' in language '{language}'")

                    except Exception as e:
                        logger.error(f"Error loading content for key '{key}' in language '{language}': {e}")
                        # Устанавливаем fallback текст
                        self.content_cache[language][key] = f"Контент не найден: {key}"

            self.is_loaded = True
            logger.info(f"Bot content loaded successfully. Languages: {list(self.content_cache.keys())}")

        except Exception as e:
            logger.error(f"Error loading bot content: {e}")
            self.is_loaded = False

    def get_content(self, key: str, language: str = "ru") -> str:
        """
        Получить контент из кэша

        Args:
            key: Ключ контента
            language: Язык (по умолчанию 'ru')

        Returns:
            Текст контента или fallback
        """
        if not self.is_loaded:
            logger.warning("Bot content not loaded yet, returning fallback")
            return f"Контент не загружен: {key}"

        language_cache = self.content_cache.get(language, {})
        content = language_cache.get(key)

        if content:
            return content  # Уже отформатирован при загрузке
        else:
            # Пытаемся загрузить контент на лету (например, упражнения)
            logger.info(f"Content not in cache, trying to load '{key}' for language '{language}'")
            return self._load_content_on_demand(key, language)

    def _load_content_on_demand(self, key: str, language: str = "ru") -> str:
        """Загрузить контент по требованию (для упражнений и других динамических ключей)"""
        try:
            import asyncio

            # Создаем новый event loop если его нет
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Загружаем контент синхронно
            if loop.is_running():
                # Если loop уже запущен, создаем task
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._async_load_content_on_demand(key, language))
                    return future.result()
            else:
                # Если loop не запущен, используем run
                return loop.run_until_complete(self._async_load_content_on_demand(key, language))

        except Exception as e:
            logger.error(f"Error loading content on demand for key '{key}': {e}")
            return f"Контент не найден: {key}"

    async def _async_load_content_on_demand(self, key: str, language: str = "ru") -> str:
        """Асинхронная загрузка контента по требованию"""
        try:
            response = await self.api_client.get_bot_content(key)
            content_text = response.get("content_text", "")

            if content_text:
                # Форматируем текст для Telegram
                formatted_text = format_text_for_telegram(content_text)

                # Кэшируем для будущего использования
                if language not in self.content_cache:
                    self.content_cache[language] = {}
                self.content_cache[language][key] = formatted_text

                logger.info(f"Loaded and cached content on demand for key '{key}' in language '{language}'")
                return formatted_text
            else:
                logger.warning(f"No content found for key '{key}' in language '{language}'")
                return f"Контент не найден: {key}"

        except Exception as e:
            logger.error(f"Error in async load content on demand for key '{key}': {e}")
            return f"Контент не найден: {key}"

    def get_welcome_message(self, language: str = "ru") -> str:
        """Получить приветственное сообщение"""
        return self.get_content("welcome_message", language)

    def get_registration_message(self, language: str = "ru") -> str:
        """Получить сообщение о регистрации"""
        return self.get_content("хочешь_тренироваться_на_этой_неделе_второе_сообщение", language)

    def get_feedback_message(self, language: str = "ru") -> str:
        """Получить сообщение об обратной связи"""
        return self.get_content("обратная_связь_для_регистрации_на_следующую_неделю", language)

    def get_exercise(self, topic_id: str, language: str = "ru") -> str:
        """Получить упражнение по теме"""
        exercise_key = f"exercise_{topic_id}"
        return self.get_content(exercise_key, language)

    async def reload_content(self):
        """Перезагрузить контент из базы данных"""
        logger.info("Reloading bot content...")
        self.is_loaded = False
        await self.load_content()

    def is_content_loaded(self) -> bool:
        """Проверить, загружен ли контент"""
        return self.is_loaded

    def get_loaded_languages(self) -> list:
        """Получить список загруженных языков"""
        return list(self.content_cache.keys())

    def get_loaded_keys(self, language: str = "ru") -> list:
        """Получить список загруженных ключей для языка"""
        return list(self.content_cache.get(language, {}).keys())
