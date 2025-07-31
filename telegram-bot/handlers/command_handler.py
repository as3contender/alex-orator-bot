"""
Обработчик команд бота
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger

from .base_handler import OratorBaseHandler
from orator_translations import get_text, get_button_text


class CommandHandler(OratorBaseHandler):
    """Обработчик команд бота"""

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
            await update.message.reply_text(welcome_text, parse_mode="MarkdownV2")

            # Отправляем сообщение о тренировке с кнопками
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
            await update.message.reply_text(training_text, reply_markup=reply_markup, parse_mode="MarkdownV2")

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

            await update.message.reply_text(help_text, parse_mode="MarkdownV2")

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
            await update.message.reply_text(training_text, reply_markup=reply_markup, parse_mode="MarkdownV2")

            logger.info(f"User {user.id} opened menu via /menu command")

        except Exception as e:
            logger.error(f"Menu command error: {e}")
            await update.message.reply_text(get_text("error_unknown", "ru"))

    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text(get_text("error_authentication", "ru"))
                return

            # Пока просто отвечаем стандартным сообщением с подсказкой о меню
            await update.message.reply_text(
                "Используйте команды бота для навигации:\n"
                "• /menu - главное меню\n"
                "• /help - справка\n"
                "• /start - перезапуск бота"
            )

        except Exception as e:
            logger.error(f"Text message handler error: {e}")
            await update.message.reply_text(get_text("error_unknown", "ru"))
