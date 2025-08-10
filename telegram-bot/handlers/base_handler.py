"""
Базовый класс для всех обработчиков
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

from loguru import logger

from orator_api_client import OratorAPIClient
from orator_translations import get_text, get_button_text
from bot_content_manager import format_text_for_telegram


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

    async def _get_user_tasks(self, user_id: int = None, language: str = "ru"):
        """Общая логика получения заданий пользователя (для команды и callback)"""
        try:
            # Получаем текущую регистрацию пользователя
            registration = await self.api_client.get_current_registration()

            if not registration:
                return None, "У вас нет активной регистрации на эту неделю. Сначала зарегистрируйтесь."

            # Получаем выбранные темы
            selected_topics = registration.get("selected_topics", [])

            if not selected_topics:
                return None, "У вас нет выбранных тем для этой недели. Сначала выберите тему при регистрации."

            # Берем первую тему
            topic_id = selected_topics[0]
            topic_tree = await self.api_client.get_topic_tree()
            topic_name = self._find_topic_name(topic_tree, topic_id)

            logger.info(f"Getting exercises for topic_id: {topic_id}")

            # Получаем упражнения по теме
            exercises_response = await self.api_client.get_exercises_by_topic(topic_id)

            if not exercises_response or not exercises_response.get("exercises"):
                return None, f"Для темы '{topic_name}' не найдено упражнений. Попробуйте выбрать другую тему."

            exercises = exercises_response["exercises"]

            return {
                "topic_id": topic_id,
                "topic_name": topic_name,
                "exercises": exercises,
                "header": f"📋 Ваши задания на эту неделю\nТема: {topic_name}\nНайдено упражнений: {len(exercises)}",
            }, None

        except Exception as e:
            logger.error(f"Error getting user tasks: {e}")
            return None, "Произошла ошибка при получении заданий."

    async def _get_user_pairs(self, user_id: int = None):
        """Получение пар пользователя"""
        try:
            pairs = await self.api_client.get_user_pairs()
            return pairs, None
        except Exception as e:
            logger.error(f"Error getting user pairs: {e}")
            return None, "Произошла ошибка при получении пар."

    async def _handle_mytasks_common(self, language: str, send_message_func, edit_message_func=None):
        """Общая логика обработки mytasks для команды и callback"""
        try:
            # Проверяем, есть ли хотя бы одна подтвержденная пара
            pairs_data, error_message = await self._get_user_pairs()
            if error_message:
                await send_message_func(error_message)
                return

            if len(pairs_data) == 0:
                await send_message_func(get_text("no_confirmed_pairs", language))
                return

            # Проверяем, есть ли подтвержденная пара
            has_confirmed_pairs = False
            for pair in pairs_data:
                if pair["status"] == "confirmed":
                    has_confirmed_pairs = True
                    break

            if not has_confirmed_pairs:
                await send_message_func(get_text("no_confirmed_pairs", language))
                return

            # Используем общую логику получения заданий
            tasks_data, error_message = await self._get_user_tasks(language)

            if error_message:
                await send_message_func(error_message)
                return

            # Отправляем заголовок
            if edit_message_func:
                await edit_message_func(tasks_data["header"])
            else:
                await send_message_func(tasks_data["header"])

            # Отправляем каждое упражнение отдельным сообщением
            for exercise in tasks_data["exercises"]:
                exercise_text = exercise["content_text"]
                formatted_text = f"{exercise_text}"

                # Разбиваем длинные сообщения (Telegram лимит ~4096 символов)
                if len(formatted_text) > 4000:
                    parts = [formatted_text[j : j + 4000] for j in range(0, len(formatted_text), 4000)]
                    for part in parts:
                        await send_message_func(part)
                else:
                    await send_message_func(formatted_text)

            # Отправляем сообщение о том, что партнер может иметь другие задания
            await send_message_func(get_text("partner_may_have_other_tasks", language))

            logger.info(f"User requested mytasks, found {len(tasks_data['exercises'])} exercises")

        except Exception as e:
            logger.error(f"MyTasks common handler error: {e}")
            await send_message_func(get_text("error_unknown", "ru"))

    def _create_main_menu_keyboard(self, language: str) -> InlineKeyboardMarkup:
        """Создает клавиатуру главного меню"""
        keyboard = [
            [
                InlineKeyboardButton(get_button_text("register", language), callback_data="register"),
                InlineKeyboardButton("📋 Задания", callback_data="mytasks"),
            ],
            [
                InlineKeyboardButton("🔍 Поиск кандидатов", callback_data="find"),
                InlineKeyboardButton("👥 Мои пары", callback_data="pairs"),
            ],
        ]

        return InlineKeyboardMarkup(keyboard)

    async def _show_main_menu_common(
        self, language: str, send_message_func, edit_message_func=None, message_text: str = None
    ):
        """Общая логика отображения главного меню"""
        from orator_translations import get_text

        if message_text is None:
            message_text = (
                get_text("main_menu_welcome", language)
                if hasattr(get_text, "main_menu_welcome")
                else "Выберите действие:"
            )

        reply_markup = self._create_main_menu_keyboard(language)

        if edit_message_func:
            await edit_message_func(message_text, reply_markup=reply_markup)
        else:
            await send_message_func(message_text, reply_markup=reply_markup)

    async def _show_main_menu_with_topics_common(
        self, language: str, send_message_func, edit_message_func=None, message_text: str = None
    ):
        """Общая логика отображения главного меню с кнопкой тем"""
        from orator_translations import get_text

        if message_text is None:
            message_text = (
                get_text("main_menu_welcome", language)
                if hasattr(get_text, "main_menu_welcome")
                else "Выберите действие:"
            )

        reply_markup = self._create_main_menu_keyboard(language)

        if edit_message_func:
            await edit_message_func(message_text, reply_markup=reply_markup)
        else:
            await send_message_func(message_text, reply_markup=reply_markup)

    def _create_back_button(self, language: str, callback_data: str = "cancel") -> InlineKeyboardButton:
        """Создает кнопку 'Назад'"""
        return InlineKeyboardButton(get_button_text("back", language), callback_data=callback_data)

    def _create_back_keyboard(self, language: str, callback_data: str = "cancel") -> InlineKeyboardMarkup:
        """Создает клавиатуру с кнопкой 'Назад'"""
        return InlineKeyboardMarkup([[self._create_back_button(language, callback_data)]])
