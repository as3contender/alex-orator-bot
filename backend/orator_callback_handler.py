from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
from datetime import datetime, timedelta

from orator_api_client import OratorAPIClient
from orator_translations import get_text, get_button_text


class OratorCallbackHandler:
    def __init__(self, api_client: OratorAPIClient, content_manager=None):
        self.api_client = api_client
        self.content_manager = content_manager
        self.selected_week = "current"  # По умолчанию текущая неделя

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
            return self.content_manager.get_content(content_key, language)

        # Fallback к API запросу
        try:
            response = await self.api_client.get_bot_content(content_key)
            return response.get("content_text", f"Контент не найден: {content_key}")
        except Exception as e:
            logger.error(f"Error getting bot content for key '{content_key}': {e}")
            # Возвращаем fallback текст
            return get_text(content_key, language)

    async def _get_exercise_by_topic(self, topic_id: str, language: str = "ru") -> str:
        """Получить упражнение по теме из кэша или базы данных"""
        if self.content_manager and self.content_manager.is_content_loaded():
            return self.content_manager.get_exercise(topic_id, language)

        # Fallback к API запросу
        try:
            response = await self.api_client.get_bot_content(f"exercise_{topic_id}")
            return response.get("content_text", f"Упражнение не найдено для темы: {topic_id}")
        except Exception as e:
            logger.error(f"Error getting exercise for topic '{topic_id}': {e}")
            return f"Упражнение для темы '{topic_id}' не найдено"

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
            elif callback_data == "cancel_registration":
                await self._handle_cancel_registration_callback(query, language)
            elif callback_data.startswith("week_"):
                await self._handle_week_selection(query, callback_data, language)
            elif callback_data.startswith("time_"):
                await self._handle_time_selection(query, callback_data, language)
            elif callback_data.startswith("topic_group_"):
                # Показать дочерние темы группы
                parent_id = callback_data.replace("topic_group_", "")
                await self._show_topics_menu(query, language, parent_id)
            elif callback_data.startswith("topic_select_"):
                # Выбрать конкретную тему
                await self._handle_topic_selection(query, callback_data, language)
            elif callback_data.startswith("candidate_"):
                await self._handle_candidate_selection(query, callback_data, language)
            elif callback_data.startswith("feedback_rating_"):
                await self._handle_feedback_rating(query, callback_data, language)
            elif callback_data.startswith("feedback_"):
                await self._handle_feedback_type_callback(query, callback_data, language)
            elif callback_data.startswith("pair_confirm_"):
                await self._handle_pair_confirm(query, callback_data, language)
            elif callback_data.startswith("pair_cancel_"):
                await self._handle_pair_cancel(query, callback_data, language)
            elif callback_data.startswith("pair_details_"):
                await self._handle_pair_details(query, callback_data, language)
            elif callback_data.startswith("pair_feedback_"):
                await self._handle_pair_feedback(query, callback_data, language)
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
            # Показываем информацию о существующей регистрации с кнопкой отмены
            keyboard = [
                [InlineKeyboardButton("❌ Отменить регистрацию", callback_data="cancel_registration")],
                [InlineKeyboardButton(get_button_text("back", language), callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Формируем текст с информацией о регистрации
            registration_text = f"У вас уже есть активная регистрация на эту неделю.\n\n"
            registration_text += f"📅 Неделя: {current_registration.get('week_start_date', 'Не указано')} - {current_registration.get('week_end_date', 'Не указано')}\n"
            registration_text += f"🕐 Время: {current_registration.get('preferred_time_msk', 'Не указано')}\n"
            registration_text += f"📝 Статус: {current_registration.get('status', 'Активна')}"

            await query.edit_message_text(registration_text, reply_markup=reply_markup, parse_mode="HTML")
            return

        # Создаем кнопки для выбора недели
        keyboard = [
            [
                InlineKeyboardButton("📅 Текущая неделя", callback_data="week_current"),
                InlineKeyboardButton("📅 Следующая неделя", callback_data="week_next"),
            ],
            [
                InlineKeyboardButton(get_button_text("cancel", language), callback_data="cancel"),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        # Получаем сообщение о регистрации из базы данных
        registration_message = await self._get_bot_content("приветственное_сообщение", language)
        await query.edit_message_text(registration_message, reply_markup=reply_markup, parse_mode="HTML")

    async def _handle_topics_callback(self, query, language: str):
        """Обработка выбора тем - показывает корневые темы"""
        logger.info("Topics callback triggered")
        try:
            await self._show_topics_menu(query, language)
        except Exception as e:
            logger.error(f"Error in topics callback: {e}")
            await query.edit_message_text("❌ Ошибка при загрузке тем. Попробуйте позже.")

    async def _show_topics_menu_after_registration(self, query, language: str):
        """Показать темы сразу после регистрации"""
        logger.info("Showing topics after registration")
        try:
            # Получаем дерево тем
            topic_tree = await self.api_client.get_topic_tree()
            logger.info(f"Topic tree received after registration: {topic_tree}")
        except Exception as e:
            logger.error(f"Error getting topic tree after registration: {e}")
            await query.edit_message_text("❌ Ошибка при загрузке тем. Попробуйте позже.")
            return

        # Показываем корневые темы
        topics_to_show = topic_tree.get("topics", [])

        # Получаем сообщение о успешной регистрации из базы данных
        registration_success_text = await self._get_bot_content(
            "хочешь_тренироваться_на_этой_неделе_второе_сообщение", language
        )
        message_text = registration_success_text + "\n\nВыберите темы для тренировки:"

        # Создаем кнопки для выбора тем
        keyboard = []
        for topic in topics_to_show:
            # Проверяем, есть ли дочерние элементы
            has_children = len(topic.get("children", [])) > 0
            if has_children:
                # Если есть дочерние элементы, показываем их
                keyboard.append(
                    [InlineKeyboardButton(f"📁 {topic['name']}", callback_data=f"topic_group_{topic['id']}")]
                )
            else:
                # Если нет дочерних элементов, это конечная тема
                keyboard.append(
                    [InlineKeyboardButton(f"✅ {topic['name']}", callback_data=f"topic_select_{topic['id']}")]
                )

        keyboard.append([InlineKeyboardButton(get_button_text("cancel", language), callback_data="main_menu")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode="HTML")

    async def _show_topics_menu(self, query, language: str, parent_id: str = None):
        """Показать меню тем (корневые или дочерние)"""
        logger.info("Getting topic tree from API")
        try:
            # Получаем дерево тем
            topic_tree = await self.api_client.get_topic_tree()
            logger.info(f"Topic tree received: {topic_tree}")
        except Exception as e:
            logger.error(f"Error getting topic tree: {e}")
            await query.edit_message_text("❌ Ошибка при загрузке тем. Попробуйте позже.")
            return

        # Определяем какие темы показывать
        if parent_id is None:
            # Показываем корневые темы
            topics_to_show = topic_tree.get("topics", [])
            message_text = get_text("topics_welcome", language)
        else:
            # Показываем дочерние темы
            topics_to_show = []
            for topic in topic_tree.get("topics", []):
                if topic["id"] == parent_id:
                    topics_to_show = topic.get("children", [])
                    break
            message_text = f"Выберите уровень для темы:"

        # Создаем кнопки для выбора тем
        keyboard = []
        for topic in topics_to_show:
            # Проверяем, есть ли дочерние элементы
            has_children = len(topic.get("children", [])) > 0
            if has_children:
                # Если есть дочерние элементы, показываем их
                keyboard.append(
                    [InlineKeyboardButton(f"📁 {topic['name']}", callback_data=f"topic_group_{topic['id']}")]
                )
            else:
                # Если нет дочерних элементов, это конечная тема
                keyboard.append(
                    [InlineKeyboardButton(f"✅ {topic['name']}", callback_data=f"topic_select_{topic['id']}")]
                )

        # Добавляем кнопку "Назад" если мы в дочерних темах
        if parent_id is not None:
            keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="topics")])

        keyboard.append([InlineKeyboardButton(get_button_text("cancel", language), callback_data="cancel")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message_text, reply_markup=reply_markup, parse_mode="HTML")

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

        # Формируем список пар как кнопки
        pairs_text = get_text("pairs_welcome", language) + "\n\nВыберите пару:"
        keyboard = []

        for i, pair in enumerate(pairs[:5], 1):
            partner_name = pair.get("partner_name", "Пользователь")
            status = pair.get("status", "unknown")
            pair_id = pair.get("id")

            status_emoji = "✅" if status == "confirmed" else "⏳" if status == "pending" else "❌"
            button_text = f"{i}. {status_emoji} {partner_name} ({status})"

            # Каждая пара - это кнопка
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"pair_details_{pair_id}")])

        keyboard.append([InlineKeyboardButton(get_button_text("back", language), callback_data="start")])
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

    async def _handle_cancel_registration_callback(self, query, language: str):
        """Обработка отмены регистрации"""
        try:
            await self.api_client.cancel_registration()
            keyboard = [
                [InlineKeyboardButton("✅ Зарегистрироваться снова", callback_data="register")],
                [InlineKeyboardButton(get_button_text("back", language), callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "✅ Регистрация успешно отменена!\n\nТеперь вы можете зарегистрироваться снова.",
                reply_markup=reply_markup,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Cancel registration error: {e}")
            keyboard = [
                [InlineKeyboardButton(get_button_text("back", language), callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Ошибка при отмене регистрации. Попробуйте позже.", reply_markup=reply_markup, parse_mode="HTML"
            )

    async def _handle_week_selection(self, query, callback_data: str, language: str):
        """Обработка выбора недели"""
        week_type = callback_data.replace("week_", "")

        # Сохраняем выбранную неделю в контексте (пока просто в переменной)
        # В реальном приложении лучше использовать FSM или кэш
        self.selected_week = week_type

        # Показываем выбор времени
        keyboard = [
            [
                InlineKeyboardButton("09:00", callback_data="time_09:00"),
                InlineKeyboardButton("10:00", callback_data="time_10:00"),
                InlineKeyboardButton("11:00", callback_data="time_11:00"),
            ],
            [
                InlineKeyboardButton("12:00", callback_data="time_12:00"),
                InlineKeyboardButton("13:00", callback_data="time_13:00"),
                InlineKeyboardButton("14:00", callback_data="time_14:00"),
            ],
            [
                InlineKeyboardButton("15:00", callback_data="time_15:00"),
                InlineKeyboardButton("16:00", callback_data="time_16:00"),
                InlineKeyboardButton("17:00", callback_data="time_17:00"),
            ],
            [
                InlineKeyboardButton("18:00", callback_data="time_18:00"),
                InlineKeyboardButton("19:00", callback_data="time_19:00"),
                InlineKeyboardButton("20:00", callback_data="time_20:00"),
            ],
            [InlineKeyboardButton(get_button_text("back", language), callback_data="register")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        week_text = "Текущая неделя" if week_type == "current" else "Следующая неделя"
        await query.edit_message_text(
            f"Выбрана неделя: {week_text}\n\nВыберите предпочитаемое время:",
            reply_markup=reply_markup,
            parse_mode="HTML",
        )

    async def _handle_time_selection(self, query, callback_data: str, language: str):
        """Обработка выбора времени"""
        # Извлекаем время из callback_data
        selected_time = callback_data.replace("time_", "")

        # Используем выбранную неделю или по умолчанию "current"
        week_type = getattr(self, "selected_week", "current")

        # Создаем регистрацию
        registration_data = {
            "week_type": week_type,
            "preferred_time_msk": selected_time,
            "selected_topics": [],
        }

        try:
            await self.api_client.register_for_week(registration_data)

            # Сразу показываем темы после успешной регистрации
            await self._show_topics_menu_after_registration(query, language)
        except Exception as e:
            logger.error(f"Registration error: {e}")
            await query.edit_message_text(get_text("registration_failed", language))

    async def _handle_topic_selection(self, query, callback_data: str, language: str):
        """Обработка выбора конкретной темы"""
        topic_id = callback_data.replace("topic_select_", "")

        # Получаем дерево тем для поиска названия темы
        topic_tree = await self.api_client.get_topic_tree()
        topic_name = self._find_topic_name(topic_tree, topic_id)

        if topic_name:
            # Получаем задание для выбранной темы
            exercise_text = await self._get_exercise_by_topic(topic_id, language)

            # Формируем сообщение с заданием
            message_text = f"✅ Тема выбрана: {topic_name}\n\n"
            message_text += f"📝 <b>Задание для тренировки:</b>\n\n"
            message_text += f"{exercise_text}\n\n"
            message_text += f"🔍 Ищем кандидатов для пары..."

            # Показываем сообщение с заданием
            await query.edit_message_text(message_text, parse_mode="HTML")

            # Автоматически запускаем поиск кандидатов
            await self._start_candidate_search(query, language)
        else:
            await query.edit_message_text("❌ Ошибка: тема не найдена", parse_mode="HTML")

    async def _start_candidate_search(self, query, language: str):
        """Запустить поиск кандидатов"""
        try:
            # Получаем текущую регистрацию
            registration = await self.api_client.get_current_registration()
            if not registration:
                await query.edit_message_text("❌ Сначала зарегистрируйтесь на неделю", parse_mode="HTML")
                return

            # Ищем кандидатов
            match_request = {"week_start_date": registration["week_start_date"], "limit": 5}
            candidates_response = await self.api_client.find_candidates(match_request)
            candidates = candidates_response.get("candidates", [])

            if not candidates:
                keyboard = [
                    [InlineKeyboardButton("🔄 Попробовать снова", callback_data="find")],
                    [InlineKeyboardButton(get_button_text("back", language), callback_data="main_menu")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(
                    "❌ Кандидаты не найдены. Попробуйте позже или измените критерии поиска.",
                    reply_markup=reply_markup,
                    parse_mode="HTML",
                )
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

                # Формируем текст кнопки
                button_text = f"{name} [{topic_display}] {preferred_time} (совпадение: {score:.1%})"

                keyboard.append([InlineKeyboardButton(button_text, callback_data=f"candidate_{candidate['user_id']}")])

            keyboard.append([InlineKeyboardButton(get_button_text("back", language), callback_data="main_menu")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                f"🎯 Найдено {len(candidates)} кандидатов для пары:\n\nВыберите кандидата:",
                reply_markup=reply_markup,
                parse_mode="HTML",
            )

        except Exception as e:
            logger.error(f"Error in candidate search: {e}")
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data="find")],
                [InlineKeyboardButton(get_button_text("back", language), callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Ошибка при поиске кандидатов. Попробуйте позже.", reply_markup=reply_markup, parse_mode="HTML"
            )

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
        else:
            # Неизвестный тип обратной связи
            await query.edit_message_text("❌ Неизвестный тип обратной связи", parse_mode="HTML")
            return

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

    async def _handle_pair_confirm(self, query, callback_data: str, language: str):
        """Обработка подтверждения пары"""
        pair_id = callback_data.replace("pair_confirm_", "")

        try:
            # Подтверждаем пару
            await self.api_client.confirm_pair(pair_id)
            await query.edit_message_text("✅ Пара подтверждена!", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Confirm pair error: {e}")
            await query.edit_message_text("❌ Ошибка при подтверждении пары", parse_mode="HTML")

    async def _handle_pair_cancel(self, query, callback_data: str, language: str):
        """Обработка отмены пары"""
        pair_id = callback_data.replace("pair_cancel_", "")

        try:
            # Отменяем пару через новый API
            await self.api_client.cancel_pair(pair_id)
            await query.edit_message_text("❌ Пара отменена", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Cancel pair error: {e}")
            await query.edit_message_text("❌ Ошибка при отмене пары", parse_mode="HTML")

    async def _handle_pair_feedback(self, query, callback_data: str, language: str):
        """Обработка обратной связи по паре"""
        pair_id = callback_data.replace("pair_feedback_", "")

        # Показываем форму для ввода обратной связи
        keyboard = [
            [InlineKeyboardButton("1 ⭐", callback_data=f"feedback_rating_{pair_id}_1")],
            [InlineKeyboardButton("2 ⭐", callback_data=f"feedback_rating_{pair_id}_2")],
            [InlineKeyboardButton("3 ⭐", callback_data=f"feedback_rating_{pair_id}_3")],
            [InlineKeyboardButton("4 ⭐", callback_data=f"feedback_rating_{pair_id}_4")],
            [InlineKeyboardButton("5 ⭐", callback_data=f"feedback_rating_{pair_id}_5")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="pairs")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "Оцените вашу тренировку с партнером:", reply_markup=reply_markup, parse_mode="HTML"
        )

    async def _handle_pair_details(self, query, callback_data: str, language: str):
        """Обработка деталей пары"""
        pair_id = callback_data.replace("pair_details_", "")

        # Получаем информацию о паре
        pairs = await self.api_client.get_user_pairs()
        target_pair = None
        for pair in pairs:
            if pair.get("id") == pair_id:
                target_pair = pair
                break

        if not target_pair:
            await query.edit_message_text("❌ Пара не найдена", parse_mode="HTML")
            return

        partner_name = target_pair.get("partner_name", "Пользователь")
        status = target_pair.get("status", "unknown")
        is_initiator = target_pair.get("is_initiator", False)

        # Формируем текст с информацией о паре
        status_emoji = "✅" if status == "confirmed" else "⏳" if status == "pending" else "❌"
        status_text = (
            "Подтверждена" if status == "confirmed" else "Ожидает подтверждения" if status == "pending" else "Отменена"
        )

        pair_info = f"👥 Пара с {partner_name}\n"
        pair_info += f"📊 Статус: {status_emoji} {status_text}\n"
        pair_info += f"🎯 Роль: {'Инициатор' if is_initiator else 'Участник'}\n"

        # Создаем кнопки действий
        keyboard = []

        if status == "pending":
            if not is_initiator:
                # Если пользователь не инициатор - может подтвердить
                keyboard.append([InlineKeyboardButton("✅ Подтвердить", callback_data=f"pair_confirm_{pair_id}")])
            # Любой может отменить
            keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data=f"pair_cancel_{pair_id}")])

        # Обратная связь доступна для всех статусов
        keyboard.append([InlineKeyboardButton("💬 Обратная связь", callback_data=f"pair_feedback_{pair_id}")])

        # Кнопка назад
        keyboard.append([InlineKeyboardButton("⬅️ Назад к парам", callback_data="pairs")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(pair_info, reply_markup=reply_markup, parse_mode="HTML")

    async def _handle_feedback_rating(self, query, callback_data: str, language: str):
        """Обработка рейтинга обратной связи"""
        # Парсим callback_data: feedback_rating_{pair_id}_{rating}
        parts = callback_data.split("_")
        pair_id = parts[2]
        rating = int(parts[3])

        try:
            # Получаем информацию о паре для определения партнера
            pairs = await self.api_client.get_user_pairs()
            target_pair = None
            for pair in pairs:
                if pair.get("id") == pair_id:
                    target_pair = pair
                    break

            if not target_pair:
                await query.edit_message_text("❌ Пара не найдена", parse_mode="HTML")
                return

            # Создаем обратную связь
            feedback_data = {
                "pair_id": pair_id,
                "rating": rating,
                "feedback_text": f"Оценка: {rating} звезд",
            }
            await self.api_client.create_feedback(feedback_data)

            await query.edit_message_text(f"✅ Спасибо за обратную связь! Оценка: {rating} ⭐", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Create feedback error: {e}")
            await query.edit_message_text("❌ Ошибка при создании обратной связи", parse_mode="HTML")
