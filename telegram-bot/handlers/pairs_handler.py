"""
Обработчик управления парами
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger

from .base_handler import OratorBaseHandler
from orator_translations import get_text, get_button_text


class PairsHandler(OratorBaseHandler):
    """Обработчик управления парами"""

    async def handle_pairs_callback(self, query, language: str):
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

        await query.edit_message_text(pairs_text, reply_markup=reply_markup, parse_mode="MarkdownV2")

    async def handle_pair_details(self, query, callback_data: str, language: str):
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
            await query.edit_message_text("❌ Пара не найдена", parse_mode="MarkdownV2")
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
        await query.edit_message_text(pair_info, reply_markup=reply_markup, parse_mode="MarkdownV2")

    async def handle_pair_confirm(self, query, callback_data: str, language: str):
        """Обработка подтверждения пары"""
        pair_id = callback_data.replace("pair_confirm_", "")

        try:
            # Подтверждаем пару
            await self.api_client.confirm_pair(pair_id)
            await query.edit_message_text("✅ Пара подтверждена!", parse_mode="MarkdownV2")
        except Exception as e:
            logger.error(f"Confirm pair error: {e}")
            await query.edit_message_text("❌ Ошибка при подтверждении пары", parse_mode="MarkdownV2")

    async def handle_pair_cancel(self, query, callback_data: str, language: str):
        """Обработка отмены пары"""
        pair_id = callback_data.replace("pair_cancel_", "")

        try:
            # Отменяем пару через новый API
            await self.api_client.cancel_pair(pair_id)
            await query.edit_message_text("❌ Пара отменена", parse_mode="MarkdownV2")
        except Exception as e:
            logger.error(f"Cancel pair error: {e}")
            await query.edit_message_text("❌ Ошибка при отмене пары", parse_mode="MarkdownV2")

    async def handle_candidate_selection(self, query, callback_data: str, language: str):
        """Обработка выбора кандидата"""
        candidate_id = callback_data.replace("candidate_", "")

        try:
            # Создаем пару
            await self.api_client.create_pair(candidate_id)
            await query.edit_message_text(get_text("pair_created", language), parse_mode="MarkdownV2")
        except Exception as e:
            logger.error(f"Create pair error: {e}")
            await query.edit_message_text(get_text("pair_failed", language))
