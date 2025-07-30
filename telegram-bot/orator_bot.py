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

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


class AlexOratorBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.api_client = OratorAPIClient(BACKEND_URL)
        self.content_manager = BotContentManager(self.api_client)
        self.command_handler = OratorCommandHandler(self.api_client, self.content_manager)
        self.callback_handler = OratorCallbackHandler(self.api_client, self.content_manager)
        self.error_handler = ErrorHandler()

        self._setup_handlers()
        self._setup_error_handler()

    def _setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""

        # Основные команды
        self.application.add_handler(CommandHandler("start", self.command_handler.start_command))
        self.application.add_handler(CommandHandler("help", self.command_handler.help_command))
        self.application.add_handler(CommandHandler("menu", self.command_handler.menu_command))

        # Обработка callback запросов (кнопки)
        self.application.add_handler(CallbackQueryHandler(self.callback_handler.handle_callback))

        # Обработка текстовых сообщений
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.command_handler.handle_text_message)
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
