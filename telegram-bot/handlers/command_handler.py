"""
Обработчик команд бота
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger

from .base_handler import OratorBaseHandler
from .feedback_handler import FeedbackHandler
from orator_translations import get_text, get_button_text
from typing import Dict, List, Any


class CommandHandler(OratorBaseHandler):
    """Обработчик команд бота"""

    def __init__(self, api_client, content_manager=None):
        super().__init__(api_client, content_manager)
        self.feedback_handler = FeedbackHandler(api_client, content_manager)

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        try:
            # Аутентификация пользователя
            if not await self._authenticate_user(update):
                await update.message.reply_text(get_text("error_authentication", "ru"))
                return

            user = update.effective_user
            language = await self._get_user_language(update)

            # Получаем контент из менеджера контента
            if self.content_manager and self.content_manager.is_content_loaded():
                # Приветственное сообщение (уже отформатировано)
                welcome_text = self.content_manager.get_content("welcome_message", language)
                logger.info(f"Welcome text (first 100 chars): {welcome_text[:100]}")

                # Сообщение о тренировке (уже отформатировано)
                training_text = self.content_manager.get_content(
                    "хочешь_тренироваться_на_этой_неделе_второе_сообщение", language
                )
                logger.info(f"Training text (first 100 chars): {training_text[:100]}")

            else:
                # Fallback к статическим текстам
                welcome_text = get_text("welcome_message", language).format(
                    name=user.first_name or user.username or "пользователь"
                )

                training_text = get_text("хочешь_тренироваться_на_этой_неделе_второе_сообщение", language)

            # Отправляем приветственное сообщение
            await update.message.reply_text(welcome_text)

            # Отправляем сообщение о тренировке с кнопками
            reply_markup = self._create_main_menu_keyboard(language)
            await update.message.reply_text(training_text, reply_markup=reply_markup)

            logger.info(f"User {user.id} started Alex Orator Bot")

        except Exception as e:
            logger.error(f"Start command error: {e}")
            await update.message.reply_text(get_text("error_unknown", "ru"))

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text(get_text("error_authentication", "ru"))
                return

            language = await self._get_user_language(update)

            # Получаем контент из менеджера контента
            if self.content_manager and self.content_manager.is_content_loaded():
                help_text = self.content_manager.get_content("help_message", language)
            else:
                # Fallback к статическому тексту
                help_text = get_text("help_message", language)

            await update.message.reply_text(help_text)

        except Exception as e:
            logger.error(f"Help command error: {e}")
            await update.message.reply_text(get_text("error_unknown", "ru"))

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /menu"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text(get_text("error_authentication", "ru"))
                return

            user = update.effective_user
            language = await self._get_user_language(update)

            # Получаем сообщение о тренировке из менеджера контента
            if self.content_manager and self.content_manager.is_content_loaded():
                training_text = self.content_manager.get_content(
                    "хочешь_тренироваться_на_этой_неделе_второе_сообщение", language
                )
            else:
                # Fallback к статическому тексту
                training_text = get_text("хочешь_тренироваться_на_этой_неделе_второе_сообщение", language)

            # Используем общую логику отображения меню
            await self._show_main_menu_common(language, update.message.reply_text, message_text=training_text)

            logger.info(f"User {user.id} opened menu via /menu command")

        except Exception as e:
            logger.error(f"Menu command error: {e}")
            await update.message.reply_text(get_text("error_unknown", "ru"))

    async def mytasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /mytasks - показывает упражнения по зарегистрированной теме"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text(get_text("error_authentication", "ru"))
                return

            user = update.effective_user
            language = await self._get_user_language(update)

            # Используем общую логику из базового класса
            await self._handle_mytasks_common(language, update.message.reply_text)

        except Exception as e:
            logger.error(f"MyTasks command error: {e}")
            await update.message.reply_text(get_text("error_unknown", "ru"))

    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text(get_text("error_authentication", "ru"))
                return

            # Обрабатываем текстовые сообщения как обычно
            await update.message.reply_text(
                "Используйте команды бота для навигации:\n"
                "• /menu - главное меню\n"
                "• /help - справка\n"
                "• /start - перезапуск бота\n"
                "• /mytasks - ваши задания на эту неделю"
            )

        except Exception as e:
            logger.error(f"Text message handler error: {e}")
            await update.message.reply_text(get_text("error_unknown", "ru"))
