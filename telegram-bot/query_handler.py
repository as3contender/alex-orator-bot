from telegram import Update
from telegram.ext import ContextTypes
from loguru import logger
import asyncio

from api_client import APIClient
from translations import get_text
from formatters import format_query_results
from exceptions import CloverdashBotException


class QueryHandler:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    async def handle_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых запросов пользователей"""
        try:
            user = update.effective_user
            query_text = update.message.text.strip()

            # Отправляем сообщение о начале обработки
            processing_message = await update.message.reply_text("🔄 Обрабатываю запрос...")

            # Аутентификация пользователя
            try:
                await self.api_client.authenticate_telegram_user(
                    telegram_id=str(user.id),
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                )
            except Exception as e:
                logger.error(f"Authentication failed for user {user.id}: {e}")
                await processing_message.edit_text("❌ Ошибка аутентификации")
                return

            # Получаем настройки пользователя
            try:
                settings = await self.api_client.get_user_settings()
                language = settings.language
            except:
                language = "ru"

            # Выполняем запрос
            try:
                # Форматируем результат
                formatted_result = format_query_results(
                    None, language, settings.show_explanations, settings.show_sql, settings.max_results
                )

                # Отправляем результат
                await processing_message.edit_text(formatted_result, parse_mode="MarkdownV2")

                logger.info(f"Query processed successfully for user {user.id}: {query_text[:50]}...")

            except Exception as e:
                logger.error(f"Query processing failed for user {user.id}: {e}")
                error_message = get_text("query_error", language)
                await processing_message.edit_text(f"❌ {error_message}")

        except Exception as e:
            logger.error(f"Query handler error: {e}")
            try:
                await processing_message.edit_text("❌ Произошла ошибка при обработке запроса")
            except:
                await update.message.reply_text("❌ Произошла ошибка при обработке запроса")

    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка callback запросов от интерактивных кнопок"""
        try:
            query = update.callback_query
            await query.answer()

            user = update.effective_user
            callback_data = query.data

            # Аутентификация пользователя
            try:
                await self.api_client.authenticate_telegram_user(
                    telegram_id=str(user.id),
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                )
            except Exception as e:
                logger.error(f"Authentication failed for user {user.id}: {e}")
                await query.edit_message_text("❌ Ошибка аутентификации")
                return

            # Получаем настройки пользователя
            try:
                settings = await self.api_client.get_user_settings()
                language = settings.language
            except:
                language = "ru"

            # Обрабатываем различные типы callback
            if callback_data.startswith("sample_query_"):
                await self._handle_sample_query(query, callback_data, language)
            elif callback_data.startswith("sample_table_"):
                await self._handle_sample_table(query, callback_data, language)
            elif callback_data == "help":
                await self._handle_help_callback(query, language)
            elif callback_data == "tables":
                await self._handle_tables_callback(query, language)
            elif callback_data == "toggle_explanations":
                await self._handle_toggle_explanations(query, settings, language)
            elif callback_data == "toggle_sql":
                await self._handle_toggle_sql(query, settings, language)
            elif callback_data == "change_language":
                await self._handle_change_language(query, language)
            elif callback_data == "reset_settings":
                await self._handle_reset_settings(query, language)
            else:
                await query.edit_message_text("❌ Неизвестная команда")

        except Exception as e:
            logger.error(f"Callback query handler error: {e}")
            try:
                await query.edit_message_text("❌ Произошла ошибка при обработке команды")
            except:
                pass

    async def _handle_sample_query(self, query, callback_data: str, language: str):
        """Обработка примера запроса"""
        sample_queries = {
            "sample_query_1": get_text("sample_query_1_text", language),
            "sample_query_2": get_text("sample_query_2_text", language),
            "sample_query_3": get_text("sample_query_3_text", language),
            "sample_query_4": get_text("sample_query_4_text", language),
        }

        sample_text = sample_queries.get(callback_data, "Покажи все данные")

        # Выполняем пример запроса
        try:
            # Форматируем результат
            formatted_result = format_query_results(None, language, True, True, 20)
            await query.edit_message_text(formatted_result, parse_mode="MarkdownV2")
        except Exception as e:
            logger.error(f"Sample query failed: {e}")
            await query.edit_message_text("❌ Ошибка при выполнении примера запроса")

    async def _handle_sample_table(self, query, callback_data: str, language: str):
        """Обработка запроса примера данных таблицы"""
        table_name = callback_data.replace("sample_table_", "")

        try:
            # Форматируем результат
            formatted_data = format_query_results(None, language, True, True, 10)
            await query.edit_message_text(formatted_data, parse_mode="MarkdownV2")
        except Exception as e:
            logger.error(f"Sample table failed: {e}")
            await query.edit_message_text("❌ Ошибка при получении примера данных")

    async def _handle_help_callback(self, query, language: str):
        """Обработка callback справки"""
        help_text = get_text("help_message", language)
        await query.edit_message_text(help_text, parse_mode="MarkdownV2")

    async def _handle_tables_callback(self, query, language: str):
        """Обработка callback списка таблиц"""
        try:
            tables = await self.api_client.get_tables()
            if not tables:
                await query.edit_message_text(get_text("no_tables", language))
                return

            # Форматируем результат
            formatted_tables = format_query_results(None, language, True, True, 0)
            await query.edit_message_text(formatted_tables, parse_mode="MarkdownV2")
        except Exception as e:
            logger.error(f"Tables callback failed: {e}")
            await query.edit_message_text("❌ Ошибка при получении списка таблиц")

    async def _handle_toggle_explanations(self, query, settings, language: str):
        """Переключение показа объяснений"""
        try:
            new_value = not settings.show_explanations
            await self.api_client.update_user_settings({"show_explanations": new_value})

            status = "включены" if new_value else "отключены"
            await query.edit_message_text(f"✅ Объяснения {status}")
        except Exception as e:
            logger.error(f"Toggle explanations failed: {e}")
            await query.edit_message_text("❌ Ошибка при изменении настроек")

    async def _handle_toggle_sql(self, query, settings, language: str):
        """Переключение показа SQL"""
        try:
            new_value = not settings.show_sql
            await self.api_client.update_user_settings({"show_sql": new_value})

            status = "включен" if new_value else "отключен"
            await query.edit_message_text(f"✅ Показ SQL {status}")
        except Exception as e:
            logger.error(f"Toggle SQL failed: {e}")
            await query.edit_message_text("❌ Ошибка при изменении настроек")

    async def _handle_change_language(self, query, language: str):
        """Смена языка"""
        new_language = "en" if language == "ru" else "ru"
        try:
            await self.api_client.update_user_settings({"language": new_language})
            await query.edit_message_text(f"✅ Язык изменен на {new_language.upper()}")
        except Exception as e:
            logger.error(f"Change language failed: {e}")
            await query.edit_message_text("❌ Ошибка при смене языка")

    async def _handle_reset_settings(self, query, language: str):
        """Сброс настроек"""
        try:
            await self.api_client.reset_user_settings()
            await query.edit_message_text("✅ Настройки сброшены к значениям по умолчанию")
        except Exception as e:
            logger.error(f"Reset settings failed: {e}")
            await query.edit_message_text("❌ Ошибка при сбросе настроек")
