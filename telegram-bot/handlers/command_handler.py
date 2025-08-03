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
            keyboard = [
                [
                    InlineKeyboardButton(get_button_text("register", language), callback_data="register"),
                    InlineKeyboardButton("📋 Задания", callback_data="mytasks"),
                ],
                [
                    InlineKeyboardButton("🔍 Поиск кандидатов", callback_data="find"),
                    InlineKeyboardButton("👥 Мои пары", callback_data="pairs"),
                ],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
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

            # Создаем интерактивные кнопки
            keyboard = [
                [
                    InlineKeyboardButton(get_button_text("register", language), callback_data="register"),
                    InlineKeyboardButton("📋 Задания", callback_data="mytasks"),
                ],
                [
                    InlineKeyboardButton("🔍 Поиск кандидатов", callback_data="find"),
                    InlineKeyboardButton("👥 Мои пары", callback_data="pairs"),
                ],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(training_text, reply_markup=reply_markup)

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
            tasks_data, error_message = await self._get_user_tasks(user.id, language)

            if error_message:
                await update.message.reply_text(error_message)
                return

            # Отправляем заголовок
            await update.message.reply_text(tasks_data["header"])

            # Отправляем каждое упражнение отдельным сообщением
            for exercise in tasks_data["exercises"]:
                exercise_text = exercise["content_text"]
                formatted_text = f"{exercise_text}"

                # Разбиваем длинные сообщения (Telegram лимит ~4096 символов)
                if len(formatted_text) > 4000:
                    # Отправляем по частям
                    parts = [formatted_text[j : j + 4000] for j in range(0, len(formatted_text), 4000)]
                    for part in parts:
                        await update.message.reply_text(part)
                else:
                    await update.message.reply_text(formatted_text)

            logger.info(f"User {user.id} requested mytasks, found {len(tasks_data['exercises'])} exercises")

        except Exception as e:
            logger.error(f"MyTasks command error: {e}")
            await update.message.reply_text(get_text("error_unknown", "ru"))

    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text(get_text("error_authentication", "ru"))
                return

            # Проверяем, может ли feedback_handler обработать это сообщение
            if hasattr(self, "feedback_handler"):
                feedback_handled = await self.feedback_handler.handle_text_message(update, context)
                if feedback_handled:
                    return  # Сообщение было обработано feedback_handler'ом

            # Если сообщение не обработано, отвечаем стандартным сообщением с подсказкой о меню
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
