"""
Обработчик обратной связи
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger

from .base_handler import OratorBaseHandler
from orator_translations import get_text, get_button_text


class FeedbackHandler(OratorBaseHandler):
    """Обработчик обратной связи"""

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
        pair_id = callback_data.replace("pair_feedback_", "")

        # Сохраняем pair_id в user_data для последующего использования
        if hasattr(query, "message") and hasattr(query.message, "reply_text"):
            # Это callback query
            await query.edit_message_text(
                f"🌟 Оцените вашу тренировку с партнером от 1 до 5:\n\n"
                f"1 - Очень плохо\n"
                f"2 - Плохо\n"
                f"3 - Нормально\n"
                f"4 - Хорошо\n"
                f"5 - Отлично\n\n"
                f"Просто отправьте цифру от 1 до 5:"
            )

        # Сохраняем состояние пользователя
        user_id = query.from_user.id
        self._set_user_feedback_state(user_id, {"stage": "waiting_rating", "pair_id": pair_id, "language": language})

    def _set_user_feedback_state(self, user_id: int, state: dict):
        """Сохраняет состояние пользователя для процесса обратной связи"""
        if not hasattr(self, "_user_feedback_states"):
            self._user_feedback_states = {}
        self._user_feedback_states[user_id] = state

    def _get_user_feedback_state(self, user_id: int):
        """Получает состояние пользователя для процесса обратной связи"""
        if not hasattr(self, "_user_feedback_states"):
            self._user_feedback_states = {}
        return self._user_feedback_states.get(user_id)

    def _clear_user_feedback_state(self, user_id: int):
        """Очищает состояние пользователя"""
        if hasattr(self, "_user_feedback_states") and user_id in self._user_feedback_states:
            del self._user_feedback_states[user_id]

    async def handle_text_message(self, update, context):
        """Обработка текстовых сообщений для обратной связи"""
        user_id = update.effective_user.id
        text = update.message.text
        state = self._get_user_feedback_state(user_id)

        if not state:
            return False  # Не наше сообщение

        try:
            if state["stage"] == "waiting_rating":
                return await self._handle_rating_input(update, text, state)
            elif state["stage"] == "waiting_comment":
                return await self._handle_comment_input(update, text, state)
        except Exception as e:
            logger.error(f"Text message handler error: {e}")
            await update.message.reply_text("❌ Произошла ошибка. Попробуйте еще раз.")
            self._clear_user_feedback_state(user_id)

        return False

    async def _handle_rating_input(self, update, text: str, state: dict):
        """Обработка ввода оценки"""
        try:
            rating = int(text.strip())
            if rating < 1 or rating > 5:
                await update.message.reply_text("❌ Пожалуйста, введите число от 1 до 5:")
                return True
        except ValueError:
            await update.message.reply_text("❌ Пожалуйста, введите число от 1 до 5:")
            return True

        # Сохраняем оценку и переходим к комментарию
        state["rating"] = rating
        state["stage"] = "waiting_comment"
        self._set_user_feedback_state(update.effective_user.id, state)

        await update.message.reply_text(
            f"✅ Оценка {rating} получена!\n\n" f"Теперь напишите комментарий о тренировке (минимум 3 символа):"
        )
        return True

    async def _handle_comment_input(self, update, text: str, state: dict):
        """Обработка ввода комментария"""
        comment = text.strip()
        if len(comment) < 3:
            await update.message.reply_text("❌ Комментарий должен содержать минимум 3 символа. Попробуйте еще раз:")
            return True

        # Сохраняем обратную связь
        try:
            feedback_data = {
                "pair_id": state["pair_id"],
                "rating": state["rating"],
                "feedback_text": comment,
            }
            await self.api_client.create_feedback(feedback_data)

            await update.message.reply_text(
                f"✅ Спасибо за обратную связь!\n" f"Оценка: {state['rating']} ⭐\n" f"Комментарий: {comment}"
            )

            # Очищаем состояние
            self._clear_user_feedback_state(update.effective_user.id)
            return True

        except Exception as e:
            logger.error(f"Create feedback error: {e}")
            await update.message.reply_text("❌ Ошибка при сохранении обратной связи")
            self._clear_user_feedback_state(update.effective_user.id)
            return True
