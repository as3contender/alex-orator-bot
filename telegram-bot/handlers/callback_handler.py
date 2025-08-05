"""
Главный обработчик callback'ов
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger

from .base_handler import OratorBaseHandler
from .registration_handler import RegistrationHandler
from .topics_handler import TopicsHandler
from .pairs_handler import PairsHandler
from .feedback_handler import FeedbackHandler

from orator_translations import get_text, get_button_text


class CallbackHandler(OratorBaseHandler):
    """Главный обработчик callback'ов"""

    def __init__(self, api_client, content_manager=None, command_handler=None):
        super().__init__(api_client, content_manager)

        # Ссылка на command_handler для переиспользования логики
        self.command_handler = command_handler

        # Инициализируем специализированные обработчики
        self.registration_handler = RegistrationHandler(api_client, content_manager)
        self.topics_handler = TopicsHandler(api_client, content_manager)
        self.pairs_handler = PairsHandler(api_client, content_manager)
        self.feedback_handler = FeedbackHandler(api_client, content_manager)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback запросов"""
        query = update.callback_query
        await query.answer()

        try:
            callback_data = query.data
            logger.info(f"CALLBACK: Received callback: {callback_data}")
            language = await self._get_user_language(update)

            # Регистрация
            if callback_data == "register":
                await self.registration_handler.handle_register_callback(query, language)
            elif callback_data == "cancel_registration":
                await self.registration_handler.handle_cancel_registration_callback(query, language)
            elif callback_data.startswith("week_"):
                await self.registration_handler.handle_week_selection(query, callback_data, language)
            elif callback_data.startswith("time_"):
                logger.info(f"CALLBACK: Processing time selection: {callback_data}")
                success = await self.registration_handler.handle_time_selection(query, callback_data, language)
                logger.info(f"CALLBACK: Time selection result: {success}")
                if success:
                    # После выбора времени показываем темы для завершения регистрации
                    logger.info("CALLBACK: Showing topics menu after time selection")
                    await self.topics_handler.show_topics_menu_after_time_selection(query, language)

            # Темы (в процессе регистрации)
            elif callback_data.startswith("reg_topic_group_"):
                # Показать дочерние темы группы в процессе регистрации
                parent_id = callback_data.replace("reg_topic_group_", "")
                logger.info(f"CALLBACK: Showing registration sub-topics for parent: {parent_id}")
                await self.topics_handler.show_registration_topics_submenu(query, language, parent_id)
            elif callback_data.startswith("reg_topic_select_"):
                # Выбрать тему в процессе регистрации
                logger.info(f"CALLBACK: Processing registration topic selection: {callback_data}")
                success = await self.topics_handler.handle_registration_topic_selection(
                    query, callback_data, language, self.registration_handler
                )
                logger.info(f"CALLBACK: Registration topic selection result: {success}")
                if success:
                    # После успешной регистрации запускаем поиск кандидатов
                    logger.info("CALLBACK: Starting candidate search after successful registration")
                    await self.topics_handler.start_candidate_search(query, language)

            # Темы (обычный просмотр)
            elif callback_data == "topics":
                await self.topics_handler.handle_topics_callback(query, language)
            elif callback_data.startswith("topic_group_"):
                # Показать дочерние темы группы
                parent_id = callback_data.replace("topic_group_", "")
                await self.topics_handler.show_topics_menu(query, language, parent_id)
            elif callback_data.startswith("topic_select_"):
                # Выбрать конкретную тему
                success = await self.topics_handler.handle_topic_selection(query, callback_data, language)
                if success:
                    # После выбора темы запускаем поиск кандидатов
                    await self.topics_handler.start_candidate_search(query, language)

            # Пары
            elif callback_data == "pairs":
                await self.pairs_handler.handle_pairs_callback(query, language)
            elif callback_data.startswith("pair_details_"):
                await self.pairs_handler.handle_pair_details(query, callback_data, language)
            elif callback_data.startswith("pair_confirm_"):
                await self.pairs_handler.handle_pair_confirm(query, callback_data, language)
            elif callback_data.startswith("pair_cancel_"):
                await self.pairs_handler.handle_pair_cancel(query, callback_data, language)
            elif callback_data.startswith("candidate_"):
                await self.pairs_handler.handle_candidate_selection(query, callback_data, language)

            # Обратная связь
            elif callback_data.startswith("pair_feedback_"):
                await self.feedback_handler.handle_pair_feedback(query, callback_data, language)
            elif callback_data.startswith("r"):
                logger.info(f"CallbackHandler: processing rating callback: {callback_data}")
                await self.feedback_handler.handle_rating_callback(query, callback_data, language)
            elif callback_data == "cancel_feedback":
                logger.info(f"CallbackHandler: processing cancel feedback callback")
                await self.feedback_handler.handle_cancel_feedback(query, language)
            elif callback_data.startswith("feedback_"):
                await self.feedback_handler.handle_feedback_type_callback(query, callback_data, language)

            # Остальные callback'ы
            elif callback_data == "find":
                await self._handle_find_callback(query, language)
            elif callback_data == "mytasks":
                await self._handle_mytasks_callback(query, context)
            elif callback_data == "profile":
                await self._handle_profile_callback(query, language)
            elif callback_data == "stats":
                await self._handle_stats_callback(query, language)
            elif callback_data == "help":
                await self._handle_help_callback(query, language)
            elif callback_data == "time_back_to_topics":
                # Возврат к корневым темам в процессе регистрации
                logger.info("CALLBACK: Returning to root topics in registration process")
                await self.topics_handler.show_topics_menu_after_time_selection(query, language)
            elif callback_data == "cancel":
                await self._handle_cancel_callback(query, language)
            else:
                await query.edit_message_text("Неизвестная команда")

        except Exception as e:
            logger.error(f"Callback handler error: {e}")
            import traceback

            logger.error(f"Callback handler traceback: {traceback.format_exc()}")
            await query.edit_message_text(get_text("error_unknown", "ru"))

    # Простые обработчики, которые остались в главном файле
    async def _handle_find_callback(self, query, language: str):
        """Обработка поиска кандидатов"""
        # Получаем текущую регистрацию
        registration = await self.api_client.get_current_registration()
        if not registration:
            await query.edit_message_text("Сначала зарегистрируйтесь на неделю: /register")
            return

        # Ищем кандидатов
        match_request = {"week_start_date": registration["week_start_date"], "limit": 5}
        candidates_response = await self.api_client.find_candidates(match_request)
        candidates = candidates_response.get("candidates", [])

        if not candidates:
            await query.edit_message_text(get_text("find_candidates_no_results", language))
            return

        # Создаем кнопки для кандидатов
        keyboard = []
        for candidate in candidates[:5]:
            name = candidate.get("name", "Пользователь")
            score = candidate.get("match_score", 0)
            preferred_time = candidate.get("preferred_time_msk", "Не указано")
            selected_topics = candidate.get("selected_topics", [])

            # Берем первую тему или показываем "Не выбрано"
            topic_display = selected_topics[0] if selected_topics else "Не выбрано"

            # Формируем текст кнопки в новом формате
            button_text = f"{name} [{topic_display}] {preferred_time} (совпадение: {score:.1%})"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"candidate_{candidate['user_id']}")])

        keyboard.append([InlineKeyboardButton(get_button_text("cancel", language), callback_data="cancel")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            get_text("find_candidates_success", language).format(count=len(candidates)), reply_markup=reply_markup
        )

    async def _handle_profile_callback(self, query, language: str):
        """Обработка профиля"""
        # Получаем профиль пользователя
        profile = await self.api_client.get_user_profile()

        profile_text = get_text("profile_welcome", language) + "\n\n"
        profile_text += f"👤 Имя: {profile.get('first_name', 'Не указано')}\n"
        profile_text += f"📧 Email: {profile.get('email', 'Не указан')}\n"
        profile_text += f"🎯 Пол: {profile.get('gender', 'Не указан')}\n"
        profile_text += f"📅 Создан: {profile.get('created_at', 'Не указано')}"

        keyboard = [[InlineKeyboardButton(get_button_text("back", language), callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(profile_text, reply_markup=reply_markup)

    async def _handle_stats_callback(self, query, language: str):
        """Обработка статистики"""
        # Получаем статистику пользователя
        stats = await self.api_client.get_user_stats()

        stats_text = get_text("stats_format", language).format(
            total_sessions=stats.get("total_sessions", 0),
            feedback_count=stats.get("feedback_count", 0),
            total_registrations=stats.get("total_registrations", 0),
            total_pairs=stats.get("total_pairs", 0),
            confirmed_pairs=stats.get("confirmed_pairs", 0),
        )

        keyboard = [[InlineKeyboardButton(get_button_text("back", language), callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(stats_text, reply_markup=reply_markup)

    async def _handle_help_callback(self, query, language: str):
        """Обработка помощи"""
        help_text = get_text("help_message", language)

        keyboard = [[InlineKeyboardButton(get_button_text("back", language), callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(help_text, reply_markup=reply_markup)

    async def _handle_cancel_callback(self, query, language: str):
        """Обработка отмены"""
        # Возвращаемся к главному меню
        await self._show_main_menu(query, language)

    async def _show_main_menu(self, query, language: str):
        """Показать главное меню"""
        # Создаем интерактивные кнопки
        keyboard = [
            [
                InlineKeyboardButton(get_button_text("register", language), callback_data="register"),
                InlineKeyboardButton("📋 Задания", callback_data="mytasks"),
            ],
            [
                InlineKeyboardButton(get_button_text("topics", language), callback_data="topics"),
                InlineKeyboardButton("🔍 Поиск кандидатов", callback_data="find"),
            ],
            [
                InlineKeyboardButton("👥 Мои пары", callback_data="pairs"),
                InlineKeyboardButton(get_button_text("help", language), callback_data="help"),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите действие:", reply_markup=reply_markup)

    async def _handle_mytasks_callback_old(self, query, context):
        """Обработка кнопки 'Задания' - переиспользует логику команды /mytasks"""
        try:
            # Аутентификация пользователя (как в base_handler)
            user = query.from_user
            await self.api_client.authenticate_telegram_user(
                telegram_id=str(user.id), username=user.username, first_name=user.first_name, last_name=user.last_name
            )

            language = await self._get_user_language_from_query(query)

            # Получаем текущую регистрацию пользователя
            registration = await self.api_client.get_current_registration()

            if not registration:
                await query.edit_message_text(
                    "У вас нет активной регистрации на эту неделю. "
                    "Сначала зарегистрируйтесь с помощью кнопки 'Зарегистрироваться'"
                )
                return

            # Получаем выбранные темы
            selected_topics = registration.get("selected_topics", [])

            if not selected_topics:
                await query.edit_message_text(
                    "У вас нет выбранных тем для этой недели. " "Сначала выберите тему при регистрации."
                )
                return

            # Берем первую тему
            topic_id = selected_topics[0]
            topic_tree = await self.api_client.get_topic_tree()
            topic_name = self._find_topic_name(topic_tree, topic_id)

            logger.info(f"Getting exercises for topic_id: {topic_id}")

            # Получаем упражнения по теме
            exercises_response = await self.api_client.get_exercises_by_topic(topic_id)

            if not exercises_response or not exercises_response.get("exercises"):
                await query.edit_message_text(
                    f"Для темы '{topic_name}' не найдено упражнений. " "Попробуйте выбрать другую тему."
                )
                return

            exercises = exercises_response["exercises"]

            # Отправляем заголовок
            await query.edit_message_text(
                f"📋 Ваши задания на эту неделю\n" f"Тема: {topic_name}\n" f"Найдено упражнений: {len(exercises)}"
            )

            # Отправляем каждое упражнение отдельным сообщением
            for i, exercise in enumerate(exercises, 1):
                exercise_text = exercise["content_text"]
                formatted_text = f"{exercise_text}"

                # Разбиваем длинные сообщения (Telegram лимит ~4096 символов)
                if len(formatted_text) > 4000:
                    parts = [formatted_text[j : j + 4000] for j in range(0, len(formatted_text), 4000)]
                    for part in parts:
                        await query.message.reply_text(part)
                else:
                    await query.message.reply_text(formatted_text)

            logger.info(f"User {user.id} requested mytasks via callback, found {len(exercises)} exercises")

        except Exception as e:
            logger.error(f"MyTasks callback error: {e}")
            await query.edit_message_text("Произошла ошибка. Попробуйте команду /mytasks")

    async def _get_user_language_from_query(self, query) -> str:
        """Получение языка пользователя для callback query"""
        try:
            settings = await self.api_client.get_user_settings()
            return settings.get("language", "ru")
        except:
            return "ru"

    async def _handle_mytasks_callback(self, query, context):
        """Обработка кнопки 'Задания' - переиспользует логику команды /mytasks"""
        try:
            # Аутентификация пользователя
            if not await self._authenticate_user_from_query(query):
                await query.edit_message_text("Ошибка аутентификации")
                return

            user = query.from_user
            language = await self._get_user_language_from_query(query)

            # Используем общую логику из базового класса
            tasks_data, error_message = await self._get_user_tasks(user.id, language)

            if error_message:
                await query.edit_message_text(error_message)
                return

            # Отправляем заголовок
            await query.edit_message_text(tasks_data["header"])

            # Отправляем каждое упражнение отдельным сообщением
            for exercise in tasks_data["exercises"]:
                exercise_text = exercise["content_text"]
                formatted_text = f"{exercise_text}"

                # Разбиваем длинные сообщения (Telegram лимит ~4096 символов)
                if len(formatted_text) > 4000:
                    parts = [formatted_text[j : j + 4000] for j in range(0, len(formatted_text), 4000)]
                    for part in parts:
                        await query.message.reply_text(part)
                else:
                    await query.message.reply_text(formatted_text)

            logger.info(
                f"User {user.id} requested mytasks via callback, found {len(tasks_data['exercises'])} exercises"
            )

        except Exception as e:
            logger.error(f"MyTasks callback error: {e}")
            await query.edit_message_text("Произошла ошибка. Попробуйте команду /mytasks")

    async def _authenticate_user_from_query(self, query) -> bool:
        """Аутентификация пользователя для callback query"""
        try:
            user = query.from_user
            await self.api_client.authenticate_telegram_user(
                telegram_id=str(user.id), username=user.username, first_name=user.first_name, last_name=user.last_name
            )
            return True
        except Exception as e:
            logger.error(f"Authentication failed for user {user.id}: {e}")
            return False
