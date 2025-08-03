"""
Обработчик работы с темами
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger

from .base_handler import OratorBaseHandler
from orator_translations import get_text, get_button_text


class TopicsHandler(OratorBaseHandler):
    """Обработчик работы с темами"""

    async def handle_topics_callback(self, query, language: str):
        """Обработка выбора тем - показывает корневые темы"""
        logger.info("Topics callback triggered")
        try:
            await self.show_topics_menu(query, language)
        except Exception as e:
            logger.error(f"Error in topics callback: {e}")
            await query.edit_message_text("❌ Ошибка при загрузке тем. Попробуйте позже.")

    async def show_topics_menu_after_time_selection(self, query, language: str):
        """Показать темы после выбора времени (в процессе регистрации)"""
        logger.info("Showing topics after time selection")
        try:
            # Получаем дерево тем
            topic_tree = await self.api_client.get_topic_tree()
            # logger.info(f"Topic tree received after time selection: {topic_tree}")
        except Exception as e:
            logger.error(f"Error getting topic tree after time selection: {e}")
            await query.edit_message_text("❌ Ошибка при загрузке тем. Попробуйте позже.")
            return

        # Показываем корневые темы (Level 1)
        topics_to_show = topic_tree.get("topics", [])

        message_text = "Выберите тему для тренировки:"

        # Создаем кнопки для выбора тем (с префиксом reg_ для отличия от обычного выбора тем)
        keyboard = []
        for topic in topics_to_show:
            # Проверяем, есть ли дочерние элементы
            has_children = len(topic.get("children", [])) > 0
            if has_children:
                # Если есть дочерние элементы, показываем их (Level 1 -> Level 2)
                keyboard.append(
                    [InlineKeyboardButton(f"📁 {topic['name']}", callback_data=f"reg_topic_group_{topic['id']}")]
                )
            else:
                # Если нет дочерних элементов, это конечная тема для регистрации (Level 1 -> регистрация)
                keyboard.append(
                    [InlineKeyboardButton(f"✅ {topic['name']}", callback_data=f"reg_topic_select_{topic['id']}")]
                )

        keyboard.append([InlineKeyboardButton(get_button_text("cancel", language), callback_data="register")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message_text, reply_markup=reply_markup)

    async def show_registration_topics_submenu(self, query, language: str, parent_id: str):
        """Показать подменю тем в процессе регистрации (Level 2)"""
        logger.info(f"TOPICS: Showing registration submenu for parent: {parent_id}")
        try:
            # Получаем дерево тем
            topic_tree = await self.api_client.get_topic_tree()
        except Exception as e:
            logger.error(f"TOPICS: Error getting topic tree for registration submenu: {e}")
            await query.edit_message_text("❌ Ошибка при загрузке тем. Попробуйте позже.")
            return

        # Находим дочерние темы для parent_id
        topics_to_show = []
        parent_name = ""
        for topic in topic_tree.get("topics", []):
            if topic["id"] == parent_id:
                topics_to_show = topic.get("children", [])
                parent_name = topic["name"]
                break

        if not topics_to_show:
            logger.warning(f"TOPICS: No sub-topics found for parent: {parent_id}")
            await query.edit_message_text("❌ Подтемы не найдены")
            return

        message_text = f"Выберите уровень для темы '{parent_name}':"

        # Создаем кнопки для выбора тем (Level 2 -> регистрация)
        keyboard = []
        for topic in topics_to_show:
            # На этом уровне все темы конечные для регистрации
            keyboard.append(
                [InlineKeyboardButton(f"✅ {topic['name']}", callback_data=f"reg_topic_select_{topic['id']}")]
            )

        # Кнопка назад к корневым темам регистрации
        keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="time_back_to_topics")])
        keyboard.append([InlineKeyboardButton(get_button_text("cancel", language), callback_data="register")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(message_text, reply_markup=reply_markup)

    async def handle_registration_topic_selection(self, query, callback_data: str, language: str, registration_handler):
        """Обработка выбора темы в процессе регистрации"""
        topic_id = callback_data.replace("reg_topic_select_", "")
        logger.info(f"TOPICS: Registration topic selection started for topic_id: {topic_id}")

        # Получаем дерево тем для поиска информации о теме
        try:
            topic_tree = await self.api_client.get_topic_tree()
            topic_info = self._find_topic_by_id(topic_tree, topic_id)
            logger.info(f"TOPICS: Topic found - ID: {topic_id}, Info: {topic_info}")
        except Exception as e:
            logger.error(f"TOPICS: Error getting topic tree: {e}")
            await query.edit_message_text("❌ Ошибка при загрузке тем")
            return False

        if topic_info:
            topic_name = topic_info["name"]
            topic_level = topic_info.get("level", 1)

            logger.info(f"TOPICS: Calling registration handler to create registration")
            # Создаем регистрацию с выбранной темой (topic_id уже содержит уровень)
            success = await registration_handler.create_registration_with_topic(topic_id)
            logger.info(f"TOPICS: Registration creation result: {success}")

            if success:
                # Проверяем level темы
                if topic_level == 2:
                    # Для тем level=2 показываем все задания
                    message_text = f"✅ Регистрация создана!\n\n"
                    message_text += f"📝 Тема: {topic_name}\n\n"
                    message_text += f"🔍 Ищем кандидатов для пары..."
                    await query.edit_message_text(message_text)

                    # Показываем все задания
                    await self._show_all_exercises_for_topic(query, topic_id, topic_name, language)
                    return True
                else:
                    # Для остальных тем показываем одно задание как обычно
                    # Получаем задание для выбранной темы
                    exercise_text = await self._get_exercise_by_topic(topic_id, language)

                    # Формируем сообщение с заданием
                    message_text = f"✅ Регистрация создана!\n\n"
                    message_text += f"📝 Тема: {topic_name}\n\n"
                    message_text += f"<b>Задание для тренировки:</b>\n\n"
                    message_text += f"{exercise_text}\n\n"
                    message_text += f"🔍 Ищем кандидатов для пары..."

                    # Показываем сообщение с заданием
                    await query.edit_message_text(message_text)
                    return True  # Успешная регистрация
            else:
                await query.edit_message_text("❌ Ошибка при создании регистрации")
                return False
        else:
            await query.edit_message_text("❌ Ошибка: тема не найдена")
            return False

    async def show_topics_menu(self, query, language: str, parent_id: str = None):
        """Показать меню тем (корневые или дочерние)"""
        logger.info("Getting topic tree from API")
        try:
            # Получаем дерево тем
            topic_tree = await self.api_client.get_topic_tree()
            # logger.info(f"Topic tree received: {topic_tree}")
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
        await query.edit_message_text(message_text, reply_markup=reply_markup)

    async def handle_topic_selection(self, query, callback_data: str, language: str):
        """Обработка выбора конкретной темы"""
        topic_id = callback_data.replace("topic_select_", "")

        # Получаем дерево тем для поиска информации о теме
        topic_tree = await self.api_client.get_topic_tree()
        topic_info = self._find_topic_by_id(topic_tree, topic_id)

        if topic_info:
            topic_name = topic_info["name"]
            topic_level = topic_info.get("level", 1)

            # Проверяем level темы
            if topic_level == 2:
                # Для тем level=2 показываем все задания
                await self._show_all_exercises_for_topic(query, topic_id, topic_name, language)
                return True
            else:
                # Для остальных тем показываем одно задание как обычно
                # Получаем задание для выбранной темы
                exercise_text = await self._get_exercise_by_topic(topic_id, language)

                # Формируем сообщение с заданием
                message_text = f"✅ Тема выбрана: {topic_name}\n\n"
                message_text += f"📝 <b>Задание для тренировки:</b>\n\n"
                message_text += f"{exercise_text}\n\n"
                message_text += f"🔍 Ищем кандидатов для пары..."

                # Показываем сообщение с заданием
                await query.edit_message_text(message_text)
                return True  # Успешный выбор темы
        else:
            await query.edit_message_text("❌ Ошибка: тема не найдена")
            return False

    async def start_candidate_search(self, query, language: str):
        """Запустить поиск кандидатов"""
        logger.info("SEARCH: Starting candidate search")
        try:
            # Получаем текущую регистрацию
            registration = await self.api_client.get_current_registration()
            logger.info(f"SEARCH: Current registration check result: {registration}")

            if not registration:
                logger.warning("SEARCH: No registration found - user needs to register first")
                await query.edit_message_text("❌ Сначала зарегистрируйтесь на неделю")
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
                    "❌ Кандидаты не найдены. Попробуйте позже или измените критерии поиска.", reply_markup=reply_markup
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
                f"🎯 Найдено {len(candidates)} кандидатов для пары:\n\nВыберите кандидата:", reply_markup=reply_markup
            )

        except Exception as e:
            logger.error(f"Error in candidate search: {e}")
            keyboard = [
                [InlineKeyboardButton("🔄 Попробовать снова", callback_data="find")],
                [InlineKeyboardButton(get_button_text("back", language), callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Ошибка при поиске кандидатов. Попробуйте позже.", reply_markup=reply_markup
            )

    def _find_topic_by_id(self, topic_tree: dict, topic_id: str) -> dict:
        """Найти полную информацию о теме по ID в дереве тем"""

        def search_in_topics(topics):
            for topic in topics:
                if topic["id"] == topic_id:
                    return topic
                # Рекурсивно ищем в дочерних темах
                if "children" in topic:
                    result = search_in_topics(topic["children"])
                    if result:
                        return result
            return None

        return search_in_topics(topic_tree.get("topics", []))

    async def _show_all_exercises_for_topic(self, query, topic_id: str, topic_name: str, language: str):
        """Показать все задания для темы level=2"""
        try:
            # Получаем все задания для темы
            exercises_response = await self.api_client.get_exercises_by_topic(topic_id)
            exercises = exercises_response.get("exercises", [])

            if not exercises:
                await query.edit_message_text(f"❌ Для темы '{topic_name}' не найдено заданий.")
                return

            # Отправляем заголовочное сообщение
            header_text = f"✅ Тема выбрана: {topic_name}\n\n"
            header_text += f"📚 Все задания по этой теме ({len(exercises)} шт.):\n\n"
            await query.edit_message_text(header_text)

            # Отправляем каждое задание отдельным сообщением
            for i, exercise in enumerate(exercises, 1):
                exercise_text = exercise.get("content_text", "Текст задания не найден")
                formatted_text = f"📝 <b>Задание {i}/{len(exercises)}:</b>\n\n{exercise_text}"

                # Разбиваем длинные сообщения (Telegram лимит ~4096 символов)
                if len(formatted_text) > 4000:
                    parts = [formatted_text[j : j + 4000] for j in range(0, len(formatted_text), 4000)]
                    for part in parts:
                        await query.message.reply_text(part)
                else:
                    await query.message.reply_text(formatted_text)

            logger.info(
                f"User {query.from_user.id} viewed all exercises for topic {topic_id}, found {len(exercises)} exercises"
            )

        except Exception as e:
            logger.error(f"Error getting exercises for topic {topic_id}: {e}")
            await query.edit_message_text(f"❌ Ошибка при загрузке заданий для темы '{topic_name}'. Попробуйте позже.")
