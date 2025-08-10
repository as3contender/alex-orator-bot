"""
Обработчик управления парами
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger

from .base_handler import OratorBaseHandler
from orator_translations import get_text, get_button_text

from telegram.constants import ParseMode

from urllib.parse import quote


def escape_html(text: str) -> str:
    """Экранирует HTML символы"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class PairsHandler(OratorBaseHandler):
    """Обработчик управления парами"""

    async def _handle_pairs_common(self, language: str, send_message_func, edit_message_func=None):
        """Общая логика обработки пар для сообщений и callback"""
        # Получаем пары пользователя
        pairs = await self.api_client.get_user_pairs()

        if not pairs:
            await send_message_func(get_text("pairs_empty", language))
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

        keyboard.append([self._create_back_button(language, "cancel")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Отправляем сообщение
        if edit_message_func:
            await edit_message_func(pairs_text, reply_markup=reply_markup)
        else:
            await send_message_func(pairs_text, reply_markup=reply_markup)

    async def handle_pairs_message(self, update, language: str):
        """Обработка текстового сообщения для просмотра пар"""
        await self._handle_pairs_common(language, update.message.reply_text)

    async def handle_pairs_callback(self, query, language: str):
        """Обработка callback для просмотра пар"""
        await self._handle_pairs_common(language, query.edit_message_text)

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
            await query.edit_message_text(
                "❌ Пара не найдена",
            )
            return

        partner_name = target_pair.get("partner_name", "Пользователь")
        status = target_pair.get("status", "unknown")
        is_initiator = target_pair.get("is_initiator", False)
        if status == "confirmed":
            username = target_pair.get("partner_username", "")
        else:
            username = ""

        # Формируем текст с информацией о паре
        status_emoji = "✅" if status == "confirmed" else "⏳" if status == "pending" else "❌"
        status_text = (
            "Подтверждена" if status == "confirmed" else "Ожидает подтверждения" if status == "pending" else "Отменена"
        )

        pair_info = f"👥 Пара с {partner_name} \n"
        if status == "confirmed":
            if username == "":
                # user_link = f"[{partner_name}](tg://user?id={target_pair['partner_telegram_id']})"
                user_link = (
                    f'<a href="tg://user?id={target_pair["partner_telegram_id"]}">{escape_html(partner_name)}</a>'
                )
            else:
                user_link = f"@{username}"
            pair_info += f"👤 Ник для связи: {user_link}\n"
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

        # Обратная связь доступна только для подтвержденных пар
        message_text = "Привет! Я от @AlexOratorBot"
        start_dialog_message = quote(message_text)

        if status == "confirmed":
            if status == "confirmed" and username:
                # Кнопка для открытия диалога с пользователем (username)
                if username == "":
                    keyboard.append(
                        [
                            InlineKeyboardButton(
                                "✉️ Написать в Telegram",
                                url=f"tg://user?id={target_pair['partner_telegram_id']}&text={start_dialog_message}",
                            )
                        ]
                    )
                else:
                    keyboard.append(
                        [
                            InlineKeyboardButton(
                                "✉️ Написать в Telegram", url=f"https://t.me/{username}?text={start_dialog_message}"
                            )
                        ]
                    )
            keyboard.append([InlineKeyboardButton("💬 Обратная связь", callback_data=f"pair_feedback_{pair_id}")])

        # Кнопка назад
        keyboard.append([InlineKeyboardButton("⬅️ Назад к парам", callback_data="pairs")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(pair_info, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    async def _handle_pair_action_common(
        self, action_func, success_message: str, error_message: str, query, language: str
    ):
        """Общая логика для действий с парами (подтверждение, отмена, создание)"""
        try:
            # Выполняем действие
            await action_func()

            # Показываем сообщение об успехе, затем список всех пар
            await query.edit_message_text(f"✅ {success_message} Загружаем ваши пары...")

            # Переиспользуем логику показа пар
            await self.handle_pairs_callback(query, language)

        except Exception as e:
            logger.error(f"Pair action error: {e}")
            await query.edit_message_text(f"❌ {error_message}")

    async def handle_pair_confirm(self, query, callback_data: str, language: str):
        """Обработка подтверждения пары"""
        pair_id = callback_data.replace("pair_confirm_", "")

        async def confirm_action():
            await self.api_client.confirm_pair(pair_id)

        await self._handle_pair_action_common(
            confirm_action, "Пара подтверждена!", "Ошибка при подтверждении пары", query, language
        )

    async def handle_pair_cancel(self, query, callback_data: str, language: str):
        """Обработка отмены пары"""
        pair_id = callback_data.replace("pair_cancel_", "")

        async def cancel_action():
            await self.api_client.cancel_pair(pair_id)

        await self._handle_pair_action_common(
            cancel_action, "Пара отменена!", "Ошибка при отмене пары", query, language
        )

    async def handle_candidate_selection(self, query, callback_data: str, language: str):
        """Обработка выбора кандидата"""
        candidate_id = callback_data.replace("candidate_", "")

        async def create_action():
            await self.api_client.create_pair(candidate_id)

        await self._handle_pair_action_common(
            create_action, "Пара создана!", get_text("pair_failed", language), query, language
        )
