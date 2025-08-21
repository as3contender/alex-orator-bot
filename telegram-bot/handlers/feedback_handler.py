"""
Обработчик обратной связи
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger

from .base_handler import OratorBaseHandler
from orator_translations import get_text, get_button_text


class FeedbackHandler(OratorBaseHandler):
    """Обработчик обратной связи"""

    # Статическое состояние для всех экземпляров класса
    _user_feedback_states = {}

    async def handle_feedback_callback(self, query, language: str):
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
        await query.edit_message_text(get_text("feedback_welcome", language), reply_markup=reply_markup)

    async def handle_feedback_type_callback(self, query, callback_data: str, language: str):
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
            await query.edit_message_text("❌ Неизвестный тип обратной связи")
            return

        keyboard = [[InlineKeyboardButton(get_button_text("back", language), callback_data="feedback")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(feedback_text, reply_markup=reply_markup)

    async def handle_pair_feedback(self, query, callback_data: str, language: str):
        """Обработка обратной связи по паре - запрос оценки"""
        logger.info(f"FeedbackHandler: handle_pair_feedback called with {callback_data}")
        pair_id = callback_data.replace("pair_feedback_", "")

        # Создаем кнопки для оценки (используем короткий pair_id)
        short_pair_id = pair_id[:8]  # Берем только первые 8 символов
        keyboard = [
            [
                InlineKeyboardButton("1 ⭐", callback_data=f"r{short_pair_id}1"),
                InlineKeyboardButton("2 ⭐⭐", callback_data=f"r{short_pair_id}2"),
                InlineKeyboardButton("3 ⭐⭐⭐", callback_data=f"r{short_pair_id}3"),
            ],
            [
                InlineKeyboardButton("4 ⭐⭐⭐⭐", callback_data=f"r{short_pair_id}4"),
                InlineKeyboardButton("5 ⭐⭐⭐⭐⭐", callback_data=f"r{short_pair_id}5"),
            ],
            [
                InlineKeyboardButton("❌ Отмена", callback_data="cancel_feedback"),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "🌟 Оцените вашу тренировку с партнером:\n\n"
            "1 - Очень плохо\n"
            "2 - Плохо\n"
            "3 - Нормально\n"
            "4 - Хорошо\n"
            "5 - Отлично",
            reply_markup=reply_markup,
        )

        # Сохраняем pair_id для последующего использования
        user_id = query.from_user.id
        short_pair_id = pair_id[:8]  # Берем только первые 8 символов
        state_data = {"pair_id": pair_id, "short_pair_id": short_pair_id, "language": language}
        self._set_user_feedback_state(user_id, state_data)
        logger.info(
            f"FeedbackHandler: set feedback state for user {user_id}, pair_id={pair_id}, short_pair_id={short_pair_id}"
        )

        # Проверяем, что состояние сохранилось
        saved_state = self._get_user_feedback_state(user_id)
        logger.info(f"FeedbackHandler: saved state verification: {saved_state}")

    async def handle_rating_callback(self, query, callback_data: str, language: str):
        """Обработка выбора оценки"""
        logger.info(f"FeedbackHandler: handle_rating_callback called with {callback_data}")

        # Парсим callback_data: r{short_pair_id}{rating}
        if not callback_data.startswith("r") or len(callback_data) != 10:
            logger.error(f"FeedbackHandler: invalid rating callback format: {callback_data}")
            await query.answer("❌ Ошибка в данных")
            return

        short_pair_id = callback_data[1:9]  # 8 символов после 'r'
        rating = int(callback_data[9])  # Последний символ - рейтинг
        logger.info(f"FeedbackHandler: parsed short_pair_id={short_pair_id}, rating={rating}")

        # Получаем полный pair_id из состояния пользователя
        user_id = query.from_user.id
        state = self._get_user_feedback_state(user_id)
        logger.info(f"FeedbackHandler: user {user_id} state in rating callback: {state}")
        if not state or state.get("short_pair_id") != short_pair_id:
            logger.error(f"FeedbackHandler: no matching state found for user {user_id}, short_pair_id={short_pair_id}")
            await query.answer("❌ Ошибка: состояние не найдено")
            return

        # Получаем полный pair_id из состояния пользователя
        user_id = query.from_user.id
        state = self._get_user_feedback_state(user_id)
        logger.info(f"FeedbackHandler: user {user_id} state in rating callback: {state}")
        if not state or state.get("short_pair_id") != short_pair_id:
            logger.error(f"FeedbackHandler: no matching state found for user {user_id}, short_pair_id={short_pair_id}")
            await query.answer("❌ Ошибка: состояние не найдено")
            return

        full_pair_id = state["pair_id"]
        logger.info(f"FeedbackHandler: using full pair_id={full_pair_id}")

        try:
            # Сохраняем обратную связь сразу после выбора рейтинга
            feedback_data = {
                "pair_id": full_pair_id,
                "rating": int(rating),
                "feedback_text": f"Оценка: {rating} звезд",
            }
            logger.info(f"FeedbackHandler: sending feedback data: {feedback_data}")
            result = await self.api_client.create_feedback(feedback_data)
            logger.info(f"FeedbackHandler: feedback saved successfully: {result}")

            await query.edit_message_text(f"✅ Спасибо за обратную связь!\n\n" f"Оценка: {rating} ⭐")

            # Очищаем состояние
            self._clear_user_feedback_state(user_id)
            logger.info(f"FeedbackHandler: feedback saved for user {user_id}, pair {full_pair_id}")

        except Exception as e:
            logger.error(f"Create feedback error: {e}")
            await query.edit_message_text("❌ Ошибка при сохранении обратной связи")

    async def handle_cancel_feedback(self, query, language: str):
        """Отмена процесса обратной связи"""
        user_id = query.from_user.id
        self._clear_user_feedback_state(user_id)

        await query.edit_message_text("❌ Обратная связь отменена")
        logger.info(f"FeedbackHandler: feedback cancelled for user {user_id}")

    def _set_user_feedback_state(self, user_id: int, state: dict):
        """Сохраняет состояние пользователя для процесса обратной связи"""
        self._user_feedback_states[user_id] = state
        logger.info(f"FeedbackHandler: _set_user_feedback_state called for user {user_id}, state: {state}")
        logger.info(f"FeedbackHandler: current states: {self._user_feedback_states}")

    def _get_user_feedback_state(self, user_id: int):
        """Получает состояние пользователя для процесса обратной связи"""
        state = self._user_feedback_states.get(user_id)
        logger.info(f"FeedbackHandler: _get_user_feedback_state called for user {user_id}, returned: {state}")
        return state

    def _clear_user_feedback_state(self, user_id: int):
        """Очищает состояние пользователя"""
        if user_id in self._user_feedback_states:
            del self._user_feedback_states[user_id]

    async def handle_text_message(self, update, context):
        """Обработка текстовых сообщений для обратной связи (больше не используется)"""
        return False
