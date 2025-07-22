from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
from datetime import datetime, timedelta

from orator_api_client import OratorAPIClient
from orator_translations import get_text, get_button_text


class OratorCallbackHandler:
    def __init__(self, api_client: OratorAPIClient):
        self.api_client = api_client

    async def _get_user_language(self, update: Update) -> str:
        """Получение языка пользователя"""
        try:
            settings = await self.api_client.get_user_settings()
            return settings.get("language", "ru")
        except:
            return "ru"

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback запросов"""
        query = update.callback_query
        await query.answer()

        try:
            callback_data = query.data
            language = await self._get_user_language(update)

            if callback_data == "register":
                await self._handle_register_callback(query, language)
            elif callback_data == "topics":
                await self._handle_topics_callback(query, language)
            elif callback_data == "find":
                await self._handle_find_callback(query, language)
            elif callback_data == "pairs":
                await self._handle_pairs_callback(query, language)
            elif callback_data == "feedback":
                await self._handle_feedback_callback(query, language)
            elif callback_data == "profile":
                await self._handle_profile_callback(query, language)
            elif callback_data == "stats":
                await self._handle_stats_callback(query, language)
            elif callback_data == "help":
                await self._handle_help_callback(query, language)
            elif callback_data == "cancel":
                await self._handle_cancel_callback(query, language)
            elif callback_data.startswith("time_"):
                await self._handle_time_selection(query, callback_data, language)
            elif callback_data.startswith("topic_"):
                await self._handle_topic_selection(query, callback_data, language)
            elif callback_data.startswith("candidate_"):
                await self._handle_candidate_selection(query, callback_data, language)
            elif callback_data.startswith("feedback_"):
                await self._handle_feedback_type_callback(query, callback_data, language)
            else:
                await query.edit_message_text("Неизвестная команда")

        except Exception as e:
            logger.error(f"Callback handler error: {e}")
            await query.edit_message_text(get_text("error_unknown", "ru"))

    async def _handle_register_callback(self, query, language: str):
        """Обработка регистрации"""
        # Проверяем, есть ли уже регистрация
        current_registration = await self.api_client.get_current_registration()
        if current_registration:
            await query.edit_message_text(get_text("registration_already_exists", language))
            return

        # Создаем кнопки для выбора времени
        keyboard = [
            [
                InlineKeyboardButton(get_text("time_morning", language), callback_data="time_morning"),
                InlineKeyboardButton(get_text("time_afternoon", language), callback_data="time_afternoon"),
            ],
            [
                InlineKeyboardButton(get_text("time_evening", language), callback_data="time_evening"),
            ],
            [
                InlineKeyboardButton(get_button_text("cancel", language), callback_data="cancel"),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            get_text("registration_welcome", language), reply_markup=reply_markup, parse_mode="HTML"
        )

    async def _handle_topics_callback(self, query, language: str):
        """Обработка выбора тем"""
        # Получаем дерево тем
        topic_tree = await self.api_client.get_topic_tree()

        # Создаем кнопки для выбора тем
        keyboard = []
        for category in topic_tree.get("categories", [])[:6]:
            keyboard.append([InlineKeyboardButton(category["name"], callback_data=f"topic_{category['id']}")])

        keyboard.append([InlineKeyboardButton(get_button_text("cancel", language), callback_data="cancel")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            get_text("topics_welcome", language), reply_markup=reply_markup, parse_mode="HTML"
        )

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
            name = candidate.get("first_name", "Пользователь")
            score = candidate.get("match_score", 0)
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{name} (совпадение: {score:.1%})", callback_data=f"candidate_{candidate['user_id']}"
                    )
                ]
            )

        keyboard.append([InlineKeyboardButton(get_button_text("cancel", language), callback_data="cancel")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            get_text("find_candidates_success", language).format(count=len(candidates)),
            reply_markup=reply_markup,
            parse_mode="HTML",
        )

    async def _handle_pairs_callback(self, query, language: str):
        """Обработка просмотра пар"""
        # Получаем пары пользователя
        pairs = await self.api_client.get_user_pairs()

        if not pairs:
            await query.edit_message_text(get_text("pairs_empty", language))
            return

        # Формируем список пар
        pairs_text = get_text("pairs_welcome", language) + "\n\n"
        for i, pair in enumerate(pairs[:5], 1):
            partner_name = pair.get("partner_name", "Пользователь")
            status = pair.get("status", "unknown")

            status_emoji = "✅" if status == "confirmed" else "⏳" if status == "pending" else "❌"
            pairs_text += f"{i}. {status_emoji} {partner_name} ({status})\n"

        keyboard = [[InlineKeyboardButton(get_button_text("back", language), callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(pairs_text, reply_markup=reply_markup, parse_mode="HTML")

    async def _handle_feedback_callback(self, query, language: str):
        """Обработка обратной связи"""
        # Создаем кнопки для обратной связи
        keyboard = [
            [
                InlineKeyboardButton("📥 Полученная", callback_data="feedback_received"),
                InlineKeyboardButton("📤 Данная", callback_data="feedback_given"),
            ],
            [
                InlineKeyboardButton(get_button_text("cancel", language), callback_data="cancel"),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            get_text("feedback_welcome", language), reply_markup=reply_markup, parse_mode="HTML"
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

        await query.edit_message_text(profile_text, reply_markup=reply_markup, parse_mode="HTML")

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

        await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode="HTML")

    async def _handle_help_callback(self, query, language: str):
        """Обработка помощи"""
        help_text = get_text("help_message", language)

        keyboard = [[InlineKeyboardButton(get_button_text("back", language), callback_data="start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode="HTML")

    async def _handle_cancel_callback(self, query, language: str):
        """Обработка отмены"""
        # Возвращаемся к главному меню
        await self._show_main_menu(query, language)

    async def _handle_time_selection(self, query, callback_data: str, language: str):
        """Обработка выбора времени"""
        time_mapping = {"time_morning": "09:00", "time_afternoon": "14:00", "time_evening": "19:00"}

        selected_time = time_mapping.get(callback_data, "14:00")

        # Получаем информацию о неделе
        week_info = await self.api_client.get_week_info()

        # Создаем регистрацию
        registration_data = {
            "week_start_date": week_info["week_start_date"],
            "week_end_date": week_info["week_end_date"],
            "preferred_time_msk": selected_time,
            "selected_topics": [],
        }

        try:
            await self.api_client.register_for_week(registration_data)
            await query.edit_message_text(get_text("registration_success", language), parse_mode="HTML")
        except Exception as e:
            logger.error(f"Registration error: {e}")
            await query.edit_message_text(get_text("registration_failed", language))

    async def _handle_topic_selection(self, query, callback_data: str, language: str):
        """Обработка выбора темы"""
        topic_id = callback_data.replace("topic_", "")

        # Здесь должна быть логика сохранения выбранной темы
        # Пока просто показываем сообщение об успехе
        await query.edit_message_text(get_text("topics_selected", language), parse_mode="HTML")

    async def _handle_candidate_selection(self, query, callback_data: str, language: str):
        """Обработка выбора кандидата"""
        candidate_id = callback_data.replace("candidate_", "")

        try:
            # Создаем пару
            await self.api_client.create_pair(candidate_id)
            await query.edit_message_text(get_text("pair_created", language), parse_mode="HTML")
        except Exception as e:
            logger.error(f"Create pair error: {e}")
            await query.edit_message_text(get_text("pair_failed", language))

    async def _handle_feedback_type_callback(self, query, callback_data: str, language: str):
        """Обработка типа обратной связи"""
        feedback_type = callback_data.replace("feedback_", "")

        if feedback_type == "received":
            feedback_list = await self.api_client.get_received_feedback()
            if not feedback_list:
                await query.edit_message_text(get_text("feedback_empty", language))
                return

            feedback_text = get_text("feedback_received", language) + "\n\n"
            for i, feedback in enumerate(feedback_list[:3], 1):
                feedback_text += f"{i}. {feedback.get('feedback_text', 'Нет текста')}\n"

        elif feedback_type == "given":
            feedback_list = await self.api_client.get_given_feedback()
            if not feedback_list:
                await query.edit_message_text(get_text("feedback_empty", language))
                return

            feedback_text = get_text("feedback_given", language) + "\n\n"
            for i, feedback in enumerate(feedback_list[:3], 1):
                feedback_text += f"{i}. {feedback.get('feedback_text', 'Нет текста')}\n"

        keyboard = [[InlineKeyboardButton(get_button_text("back", language), callback_data="feedback")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(feedback_text, reply_markup=reply_markup, parse_mode="HTML")

    async def _show_main_menu(self, query, language: str):
        """Показать главное меню"""
        # Создаем интерактивные кнопки
        keyboard = [
            [
                InlineKeyboardButton(get_button_text("register", language), callback_data="register"),
                InlineKeyboardButton(get_button_text("topics", language), callback_data="topics"),
            ],
            [
                InlineKeyboardButton(get_button_text("find", language), callback_data="find"),
                InlineKeyboardButton(get_button_text("pairs", language), callback_data="pairs"),
            ],
            [
                InlineKeyboardButton(get_button_text("feedback", language), callback_data="feedback"),
                InlineKeyboardButton(get_button_text("profile", language), callback_data="profile"),
            ],
            [
                InlineKeyboardButton(get_button_text("stats", language), callback_data="stats"),
                InlineKeyboardButton(get_button_text("help", language), callback_data="help"),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите действие:", reply_markup=reply_markup, parse_mode="HTML")
