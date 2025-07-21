from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger

from api_client import APIClient
from translations import get_text
from formatters import format_tables_list, format_sample_data, format_settings
from exceptions import CloverdashBotException


class CommandHandlers:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client

    async def _authenticate_user(self, update: Update) -> bool:
        """Аутентификация пользователя через Telegram"""
        try:
            user = update.effective_user
            await self.api_client.authenticate_telegram_user(
                telegram_id=str(user.id), username=user.username, first_name=user.first_name, last_name=user.last_name
            )
            return True
        except Exception as e:
            logger.error(f"Authentication failed for user {user.id}: {e}")
            return False

    async def _get_user_language(self, update: Update) -> str:
        """Получение языка пользователя"""
        try:
            settings = await self.api_client.get_user_settings()
            return settings.language
        except:
            return "ru"

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        try:
            # Аутентификация пользователя
            if not await self._authenticate_user(update):
                await update.message.reply_text("❌ Ошибка аутентификации")
                return

            user = update.effective_user
            language = await self._get_user_language(update)

            # Приветственное сообщение
            welcome_text = get_text("welcome_message", language).format(
                name=user.first_name or user.username or "пользователь"
            )

            # Создаем интерактивные кнопки с примерами запросов
            keyboard = [
                [
                    InlineKeyboardButton(get_text("sample_query_1", language), callback_data="sample_query_1"),
                    InlineKeyboardButton(get_text("sample_query_2", language), callback_data="sample_query_2"),
                ],
                [
                    InlineKeyboardButton(get_text("sample_query_3", language), callback_data="sample_query_3"),
                    InlineKeyboardButton(get_text("sample_query_4", language), callback_data="sample_query_4"),
                ],
                [
                    InlineKeyboardButton(get_text("help_button", language), callback_data="help"),
                    InlineKeyboardButton(get_text("tables_button", language), callback_data="tables"),
                ],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")

            logger.info(f"User {user.id} started the bot")

        except Exception as e:
            logger.error(f"Start command error: {e}")
            await update.message.reply_text("❌ Произошла ошибка при запуске бота")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text("❌ Ошибка аутентификации")
                return

            language = await self._get_user_language(update)
            help_text = get_text("help_message", language)

            await update.message.reply_text(help_text, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Help command error: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении справки")

    async def tables_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /tables"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text("❌ Ошибка аутентификации")
                return

            language = await self._get_user_language(update)

            # Получаем список таблиц
            tables = await self.api_client.get_tables()

            if not tables:
                await update.message.reply_text(get_text("no_tables", language))
                return

            # Форматируем список таблиц
            tables_text = format_tables_list(tables, language)

            await update.message.reply_text(tables_text, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Tables command error: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении списка таблиц")

    async def sample_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /sample"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text("❌ Ошибка аутентификации")
                return

            language = await self._get_user_language(update)

            # Получаем список таблиц для выбора
            tables = await self.api_client.get_tables()

            if not tables:
                await update.message.reply_text(get_text("no_tables", language))
                return

            # Создаем кнопки для выбора таблицы
            keyboard = []
            for table in tables[:10]:  # Ограничиваем 10 таблицами
                keyboard.append([InlineKeyboardButton(f"📊 {table.name}", callback_data=f"sample_table_{table.name}")])

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(get_text("select_table_for_sample", language), reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Sample command error: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении примеров данных")

    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /settings"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text("❌ Ошибка аутентификации")
                return

            language = await self._get_user_language(update)

            # Получаем текущие настройки
            settings = await self.api_client.get_user_settings()

            # Форматируем настройки
            settings_text = format_settings(settings, language)

            # Создаем кнопки для изменения настроек
            keyboard = [
                [
                    InlineKeyboardButton(
                        get_text("toggle_explanations", language), callback_data="toggle_explanations"
                    ),
                    InlineKeyboardButton(get_text("toggle_sql", language), callback_data="toggle_sql"),
                ],
                [
                    InlineKeyboardButton(get_text("change_language", language), callback_data="change_language"),
                    InlineKeyboardButton(get_text("reset_settings", language), callback_data="reset_settings"),
                ],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(settings_text, reply_markup=reply_markup, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Settings command error: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении настроек")

    async def quick_language_en(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Быстрая смена языка на английский"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text("❌ Authentication error")
                return

            await self.api_client.update_user_settings({"language": "en"})
            await update.message.reply_text("✅ Language changed to English")

        except Exception as e:
            logger.error(f"Quick language EN error: {e}")
            await update.message.reply_text("❌ Error changing language")

    async def quick_language_ru(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Быстрая смена языка на русский"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text("❌ Ошибка аутентификации")
                return

            await self.api_client.update_user_settings({"language": "ru"})
            await update.message.reply_text("✅ Язык изменен на русский")

        except Exception as e:
            logger.error(f"Quick language RU error: {e}")
            await update.message.reply_text("❌ Ошибка смены языка")
