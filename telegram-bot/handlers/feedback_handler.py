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
        await query.edit_message_text(
            get_text("feedback_welcome", language), reply_markup=reply_markup, parse_mode="HTML"
        )

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
            await query.edit_message_text("❌ Неизвестный тип обратной связи", parse_mode="HTML")
            return

        keyboard = [[InlineKeyboardButton(get_button_text("back", language), callback_data="feedback")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(feedback_text, reply_markup=reply_markup, parse_mode="HTML")

    async def handle_pair_feedback(self, query, callback_data: str, language: str):
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

    async def handle_feedback_rating(self, query, callback_data: str, language: str):
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
