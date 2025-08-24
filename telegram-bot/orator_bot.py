import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from loguru import logger

from config import BOT_TOKEN, BACKEND_URL
from handlers import CommandHandler as OratorCommandHandler, CallbackHandler as OratorCallbackHandler
from error_handler import ErrorHandler
from orator_api_client import OratorAPIClient
from bot_content_manager import BotContentManager

from telegram import ReplyKeyboardMarkup, KeyboardButton

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


class AlexOratorBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.api_client = OratorAPIClient(BACKEND_URL)
        self.content_manager = BotContentManager(self.api_client)
        self.command_handler = OratorCommandHandler(self.api_client, self.content_manager)
        self.callback_handler = OratorCallbackHandler(self.api_client, self.content_manager, self.command_handler)
        self.error_handler = ErrorHandler()

        self._setup_handlers()
        self._setup_error_handler()

    def _setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""

        # Основные команды
        self.application.add_handler(CommandHandler("start", self.command_handler.start_command))
        self.application.add_handler(CommandHandler("help", self.command_handler.help_command))
        self.application.add_handler(CommandHandler("menu", self.command_handler.menu_command))
        self.application.add_handler(CommandHandler("mytasks", self.command_handler.mytasks_command))

        # Команды поиска и пар
        self.application.add_handler(CommandHandler("find", self.command_handler.find_command))
        self.application.add_handler(CommandHandler("pairs", self.command_handler.pairs_command))

        # Обработка меню
        self.menu_keyboard = self._build_menu_keyboard()
        self._setup_menu_handler()

        # Обработка callback запросов (кнопки)
        self.application.add_handler(CallbackQueryHandler(self.callback_handler.handle_callback))

        # Обработка текстовых сообщений
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.command_handler.handle_text_message)
        )

    def _setup_error_handler(self):
        """Настройка обработчика ошибок"""
        self.application.add_error_handler(self.error_handler.handle_error)

    def _build_menu_keyboard(self) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            [
                [KeyboardButton("🚀 Зарегистрироваться"), KeyboardButton("👥 Мои пары")],
                [KeyboardButton("🔍 Поиск кандидатов"), KeyboardButton("🗒 Мои задачи")],
                [KeyboardButton("🔄 Перезапуск бота"), KeyboardButton("❓ Помощь")],
            ],
            resize_keyboard=True,
            one_time_keyboard=False,
        )

    def _setup_menu_handler(self):
        """Настройка обработчика меню"""
        self.application.add_handler(
            MessageHandler(filters.TEXT & filters.Regex(r"^👥 Мои пары$"), self._handle_pairs_message)
        )
        self.application.add_handler(
            MessageHandler(filters.TEXT & filters.Regex(r"^🗒 Мои задачи$"), self._handle_mytasks_message)
        )
        self.application.add_handler(
            MessageHandler(filters.TEXT & filters.Regex(r"^🚀 Зарегистрироваться$"), self._handle_register_message)
        )
        self.application.add_handler(
            MessageHandler(filters.TEXT & filters.Regex(r"^❓ Помощь$"), self._handle_help_message)
        )
        self.application.add_handler(
            MessageHandler(filters.TEXT & filters.Regex(r"^🔍 Поиск кандидатов$"), self._handle_find_candidates_message)
        )
        self.application.add_handler(
            MessageHandler(filters.TEXT & filters.Regex(r"^🔄 Перезапуск бота$"), self._handle_restart_bot_message)
        )

    async def _handle_find_candidates_message(self, update, context):
        """Обработчик текстового сообщения для поиска кандидатов"""
        try:
            # Аутентификация пользователя
            if not await self.command_handler._authenticate_user(update):
                await update.message.reply_text("Ошибка аутентификации")
                return

            language = await self.command_handler._get_user_language(update)

            # Используем find_candidates_handler для обработки
            # Создаем mock query для совместимости с callback handler
            from telegram import CallbackQuery

            mock_query = type(
                "MockQuery",
                (),
                {
                    "edit_message_text": update.message.reply_text,
                    "message": update.message,
                    "from_user": update.effective_user,
                },
            )()
            await self.callback_handler._handle_find_callback(mock_query, language)

        except Exception as e:
            logger.error(f"Find candidates message handler error: {e}")
            await update.message.reply_text("Произошла ошибка при обработке запроса")

    async def _handle_restart_bot_message(self, update, context):
        """Обработчик текстового сообщения для перезапуска бота"""
        try:
            # Аутентификация пользователя
            if not await self.command_handler._authenticate_user(update):
                await update.message.reply_text("Ошибка аутентификации")
                return

            # Используем restart_bot_handler для обработки
            await self.command_handler.start_command(update, context)

        except Exception as e:
            logger.error(f"Restart bot message handler error: {e}")
            await update.message.reply_text("Произошла ошибка при обработке запроса")

    async def _handle_pairs_message(self, update, context):
        """Обработчик текстового сообщения для пар"""
        try:
            # Аутентификация пользователя
            if not await self.command_handler._authenticate_user(update):
                await update.message.reply_text("Ошибка аутентификации")
                return

            language = await self.command_handler._get_user_language(update)

            # Используем pairs_handler для обработки
            await self.callback_handler.pairs_handler.handle_pairs_message(update, language)

        except Exception as e:
            logger.error(f"Pairs message handler error: {e}")
            await update.message.reply_text("Произошла ошибка при обработке запроса")

    async def _handle_mytasks_message(self, update, context):
        """Обработчик текстового сообщения для заданий"""
        try:
            # Аутентификация пользователя
            if not await self.command_handler._authenticate_user(update):
                await update.message.reply_text("Ошибка аутентификации")
                return

            language = await self.command_handler._get_user_language(update)

            # Используем общую логику из command_handler
            await self.command_handler._handle_mytasks_common(language, update.message.reply_text)

        except Exception as e:
            logger.error(f"MyTasks message handler error: {e}")
            await update.message.reply_text("Произошла ошибка при обработке запроса")

    async def _handle_register_message(self, update, context):
        """Обработчик текстового сообщения для регистрации"""
        try:
            # Аутентификация пользователя
            if not await self.command_handler._authenticate_user(update):
                await update.message.reply_text("Ошибка аутентификации")
                return

            language = await self.command_handler._get_user_language(update)

            # Создаем mock query для совместимости с callback handler
            from telegram import CallbackQuery

            mock_query = type(
                "MockQuery",
                (),
                {
                    "edit_message_text": update.message.reply_text,
                    "message": update.message,
                    "from_user": update.effective_user,
                },
            )()

            # Используем registration_handler для обработки
            await self.callback_handler.registration_handler.handle_register_callback(mock_query, language)

        except Exception as e:
            logger.error(f"Register message handler error: {e}")
            await update.message.reply_text("Произошла ошибка при обработке запроса")

    async def _handle_help_message(self, update, context):
        """Обработчик текстового сообщения для помощи"""
        try:
            # Аутентификация пользователя
            if not await self.command_handler._authenticate_user(update):
                await update.message.reply_text("Ошибка аутентификации")
                return

            language = await self.command_handler._get_user_language(update)

            # Используем command_handler для обработки
            await self.command_handler.help_command(update, context)

        except Exception as e:
            logger.error(f"Help message handler error: {e}")
            await update.message.reply_text("Произошла ошибка при обработке запроса")

    async def start(self):
        """Запуск бота"""
        logger.info("Starting Alex Orator Bot...")

        # Проверка подключения к backend
        try:
            await self.api_client.check_connection()
            logger.info("Backend connection successful")
        except Exception as e:
            logger.error(f"Backend connection failed: {e}")
            raise

        # Загружаем контент бота
        try:
            await self.content_manager.load_content()
            logger.info("Bot content loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load bot content: {e}")
            # Продолжаем работу без контента

        # Запуск бота
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(allowed_updates=Update.ALL_TYPES)

        # Держим бота запущенным
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    async def stop(self):
        """Остановка бота"""
        logger.info("Stopping Alex Orator Bot...")
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()


async def main():
    """Главная функция"""
    bot = AlexOratorBot()
    started = False

    try:
        await bot.start()
        started = True
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        if started:
            await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
