from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger

from exceptions import CloverdashBotException, BackendConnectionError, AuthenticationError


class ErrorHandler:
    def handle_error(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Централизованная обработка ошибок"""
        try:
            # Логируем ошибку
            logger.error(f"Exception while handling an update: {context.error}")

            # Определяем тип ошибки и отправляем соответствующее сообщение
            if isinstance(context.error, BackendConnectionError):
                error_message = "❌ Ошибка подключения к серверу. Попробуйте позже."
            elif isinstance(context.error, AuthenticationError):
                error_message = "❌ Ошибка аутентификации. Попробуйте перезапустить бота командой /start"
            elif isinstance(context.error, CloverdashBotException):
                error_message = f"❌ Ошибка: {context.error}"
            else:
                error_message = "❌ Произошла непредвиденная ошибка. Попробуйте позже."

            # Отправляем сообщение об ошибке пользователю
            if update and hasattr(update, "effective_chat"):
                try:
                    context.bot.send_message(chat_id=update.effective_chat.id, text=error_message)
                except Exception as e:
                    logger.error(f"Failed to send error message: {e}")

        except Exception as e:
            logger.error(f"Error in error handler: {e}")
