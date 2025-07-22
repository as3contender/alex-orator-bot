import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from loguru import logger

from config import BOT_TOKEN, BACKEND_URL
from orator_handlers import OratorCommandHandlers
from orator_callback_handler import OratorCallbackHandler
from error_handler import ErrorHandler
from orator_api_client import OratorAPIClient

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


class AlexOratorBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.api_client = OratorAPIClient(BACKEND_URL)
        self.command_handlers = OratorCommandHandlers(self.api_client)
        self.callback_handler = OratorCallbackHandler(self.api_client)
        self.error_handler = ErrorHandler()

        self._setup_handlers()
        self._setup_error_handler()

    def _setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""

        # Основные команды
        self.application.add_handler(CommandHandler("start", self.command_handlers.start_command))
        self.application.add_handler(CommandHandler("help", self.command_handlers.help_command))
        self.application.add_handler(CommandHandler("profile", self.command_handlers.profile_command))
        self.application.add_handler(CommandHandler("register", self.command_handlers.register_command))
        self.application.add_handler(CommandHandler("topics", self.command_handlers.topics_command))
        self.application.add_handler(CommandHandler("find", self.command_handlers.find_candidates_command))
        self.application.add_handler(CommandHandler("pairs", self.command_handlers.pairs_command))
        self.application.add_handler(CommandHandler("feedback", self.command_handlers.feedback_command))
        self.application.add_handler(CommandHandler("stats", self.command_handlers.stats_command))
        self.application.add_handler(CommandHandler("cancel", self.command_handlers.cancel_registration_command))

        # Быстрые команды для смены языка
        self.application.add_handler(CommandHandler("en", self.command_handlers.quick_language_en))
        self.application.add_handler(CommandHandler("ru", self.command_handlers.quick_language_ru))

        # Обработка callback запросов (кнопки)
        self.application.add_handler(CallbackQueryHandler(self.callback_handler.handle_callback))

        # Обработка текстовых сообщений (для выбора тем, времени и т.д.)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.command_handlers.handle_text_message)
        )

    def _setup_error_handler(self):
        """Настройка обработчика ошибок"""
        self.application.add_error_handler(self.error_handler.handle_error)

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
