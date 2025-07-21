import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from loguru import logger

from config import BOT_TOKEN, BACKEND_URL
from handlers import CommandHandlers
from query_handler import QueryHandler
from error_handler import ErrorHandler
from api_client import APIClient

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


class CloverdashBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.api_client = APIClient(BACKEND_URL)
        self.command_handlers = CommandHandlers(self.api_client)
        self.query_handler = QueryHandler(self.api_client)
        self.error_handler = ErrorHandler()

        self._setup_handlers()
        self._setup_error_handler()

    def _setup_handlers(self):
        """Настройка обработчиков команд и сообщений"""

        # Команды
        self.application.add_handler(CommandHandler("start", self.command_handlers.start_command))
        self.application.add_handler(CommandHandler("help", self.command_handlers.help_command))
        self.application.add_handler(CommandHandler("tables", self.command_handlers.tables_command))
        self.application.add_handler(CommandHandler("sample", self.command_handlers.sample_command))
        self.application.add_handler(CommandHandler("settings", self.command_handlers.settings_command))

        # Быстрые команды для смены языка
        self.application.add_handler(CommandHandler("en", self.command_handlers.quick_language_en))
        self.application.add_handler(CommandHandler("ru", self.command_handlers.quick_language_ru))

        # Обработка текстовых сообщений (запросы на естественном языке)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.query_handler.handle_query))

    def _setup_error_handler(self):
        """Настройка обработчика ошибок"""
        self.application.add_error_handler(self.error_handler.handle_error)

    async def start(self):
        """Запуск бота"""
        logger.info("Starting CloverdashBot...")

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
        await self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def stop(self):
        """Остановка бота"""
        logger.info("Stopping CloverdashBot...")
        await self.application.stop()
        await self.application.shutdown()


async def main():
    """Главная функция"""
    bot = CloverdashBot()

    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
