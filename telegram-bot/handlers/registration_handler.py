"""
Обработчик регистрации пользователей
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger

from .base_handler import OratorBaseHandler
from orator_translations import get_button_text


class RegistrationHandler(OratorBaseHandler):
    """Обработчик регистрации пользователей"""

    def __init__(self, api_client, content_manager=None):
        super().__init__(api_client, content_manager)
        self.selected_week = "current"  # По умолчанию текущая неделя

    async def handle_register_callback(self, query, language: str):
        """Обработка регистрации"""
        logger.info("=== REGISTRATION: Starting registration process ===")
        # Проверяем, есть ли уже регистрация
        try:
            current_registration = await self.api_client.get_current_registration()
            logger.info(f"REGISTRATION: Current registration check result: {current_registration}")
        except Exception as e:
            logger.error(f"REGISTRATION: Error checking current registration: {e}")
            current_registration = None
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

            await query.edit_message_text(registration_text, reply_markup=reply_markup)
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
        registration_message = await self._get_bot_content("chat_rules", language)
        await query.edit_message_text(registration_message, reply_markup=reply_markup)

    async def handle_week_selection(self, query, callback_data: str, language: str):
        """Обработка выбора недели"""
        week_type = callback_data.replace("week_", "")
        logger.info(f"REGISTRATION: Week selected: {week_type}")

        # Сохраняем выбранную неделю в контексте (пока просто в переменной)
        # В реальном приложении лучше использовать FSM или кэш
        self.selected_week = week_type
        logger.info(f"REGISTRATION: Selected week saved: {self.selected_week}")

        # Показываем выбор времени
        keyboard = [
            [
                InlineKeyboardButton("🕗 Утро (6:00–11:59)", callback_data="time_06:00"),
                InlineKeyboardButton("🌞 День (12:00–17:59)", callback_data="time_12:00"),
            ],
            [
                InlineKeyboardButton("🌇 Вечер (18:00–23:59)", callback_data="time_18:00"),
                InlineKeyboardButton("🌙 Ночь (00:00–05:59)", callback_data="time_00:00"),
            ],
            [InlineKeyboardButton(get_button_text("back", language), callback_data="register")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        week_text = "Текущая неделя" if week_type == "current" else "Следующая неделя"
        await query.edit_message_text(
            f"Выбрана неделя: {week_text}\n\nВыберите предпочитаемое время.\n\n❗️Это лишь желаемое время – о точном нужно договориться с партнёром в переписке",
            reply_markup=reply_markup,
        )

    async def handle_time_selection(self, query, callback_data: str, language: str):
        """Обработка выбора времени"""
        # Извлекаем время из callback_data
        selected_time = callback_data.replace("time_", "")
        logger.info(f"REGISTRATION: Time selected: {selected_time}")

        # Сохраняем выбранное время
        self.selected_time = selected_time
        logger.info(f"REGISTRATION: Selected time saved: {self.selected_time}")

        # После выбора времени переходим к выбору темы
        message_text = f"✅ Время выбрано: {selected_time}\n\nТеперь выберите тему для тренировки:"

        # Показываем сообщение и возвращаем True для перехода к темам
        await query.edit_message_text(
            message_text,
        )
        return True  # Переходим к выбору тем

    async def create_registration_with_topic(self, topic_id: str):
        """Создание регистрации с выбранной темой"""
        logger.info(f"REGISTRATION: Starting registration creation with topic: {topic_id}")

        # Используем сохраненные данные
        week_type = getattr(self, "selected_week", "current")
        selected_time = getattr(self, "selected_time", "10:00")

        logger.info(f"REGISTRATION: Retrieved saved data - week: {week_type}, time: {selected_time}")

        # Создаем регистрацию с выбранной темой (topic_id уже содержит уровень)
        registration_data = {
            "week_type": week_type,
            "preferred_time_msk": selected_time,
            "selected_topics": [topic_id],
        }

        logger.info(f"REGISTRATION: Registration data prepared: {registration_data}")

        try:
            result = await self.api_client.register_for_week(registration_data)
            logger.info(f"REGISTRATION: API call successful. Result: {result}")
            logger.info(f"REGISTRATION: Registration created successfully with topic {topic_id}")
            return True
        except Exception as e:
            logger.error(f"REGISTRATION: Registration error: {e}")
            return False

    async def handle_cancel_registration_callback(self, query, language: str):
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
            )
        except Exception as e:
            logger.error(f"Cancel registration error: {e}")
            keyboard = [
                [InlineKeyboardButton(get_button_text("back", language), callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(
                "❌ Ошибка при отмене регистрации. Попробуйте позже.", reply_markup=reply_markup
            )
