from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from loguru import logger
from datetime import datetime, timedelta

from orator_api_client import OratorAPIClient
from orator_translations import get_text, get_button_text
from exceptions import CloverdashBotException


class OratorCommandHandlers:
    def __init__(self, api_client: OratorAPIClient):
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
            return settings.get("language", "ru")
        except:
            return "ru"

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        try:
            # Аутентификация пользователя
            if not await self._authenticate_user(update):
                await update.message.reply_text(get_text("error_authentication", "ru"))
                return

            user = update.effective_user
            language = await self._get_user_language(update)

            # Приветственное сообщение
            welcome_text = get_text("welcome_message", language).format(
                name=user.first_name or user.username or "пользователь"
            )

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
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="HTML")

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
            help_text = get_text("help_message", language)

            await update.message.reply_text(help_text, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Help command error: {e}")
            await update.message.reply_text(get_text("error_unknown", "ru"))

    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /register"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text(get_text("error_authentication", "ru"))
                return

            language = await self._get_user_language(update)

            # Проверяем, есть ли уже регистрация
            current_registration = await self.api_client.get_current_registration()
            if current_registration:
                await update.message.reply_text(get_text("registration_already_exists", language))
                return

            # Получаем информацию о неделе
            week_info = await self.api_client.get_week_info()

            # Создаем кнопки для выбора времени
            keyboard = [
                [
                    InlineKeyboardButton(get_text("time_morning", language), callback_data="time_morning"),
                    InlineKeyboardButton(get_text("time_afternoon", language), callback_data="time_afternoon"),
                ],
                [
                    InlineKeyboardButton(get_text("time_evening", language), callback_data="time_evening"),
                ],
                [
                    InlineKeyboardButton(get_button_text("cancel", language), callback_data="cancel"),
                ],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                get_text("registration_welcome", language), reply_markup=reply_markup, parse_mode="HTML"
            )

        except Exception as e:
            logger.error(f"Register command error: {e}")
            await update.message.reply_text(get_text("error_unknown", "ru"))

    async def topics_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /topics"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text(get_text("error_authentication", "ru"))
                return

            language = await self._get_user_language(update)

            # Получаем дерево тем
            topic_tree = await self.api_client.get_topic_tree()

            # Создаем кнопки для выбора тем (упрощенная версия)
            keyboard = []
            for category in topic_tree.get("categories", [])[:6]:  # Ограничиваем количество
                keyboard.append([InlineKeyboardButton(category["name"], callback_data=f"topic_{category['id']}")])

            keyboard.append([InlineKeyboardButton(get_button_text("cancel", language), callback_data="cancel")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                get_text("topics_welcome", language), reply_markup=reply_markup, parse_mode="HTML"
            )

        except Exception as e:
            logger.error(f"Topics command error: {e}")
            await update.message.reply_text(get_text("error_unknown", "ru"))

    async def find_candidates_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /find"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text(get_text("error_authentication", "ru"))
                return

            language = await self._get_user_language(update)

            # Получаем текущую регистрацию
            registration = await self.api_client.get_current_registration()
            if not registration:
                await update.message.reply_text("Сначала зарегистрируйтесь на неделю: /register")
                return

            # Ищем кандидатов
            match_request = {"week_start_date": registration["week_start_date"], "limit": 5}

            candidates_response = await self.api_client.find_candidates(match_request)
            candidates = candidates_response.get("candidates", [])

            if not candidates:
                await update.message.reply_text(get_text("find_candidates_no_results", language))
                return

            # Создаем кнопки для кандидатов
            keyboard = []
            for candidate in candidates[:5]:  # Ограничиваем количество
                name = candidate.get("first_name", "Пользователь")
                score = candidate.get("match_score", 0)
                keyboard.append(
                    [
                        InlineKeyboardButton(
                            f"{name} (совпадение: {score:.1%})", callback_data=f"candidate_{candidate['user_id']}"
                        )
                    ]
                )

            keyboard.append([InlineKeyboardButton(get_button_text("cancel", language), callback_data="cancel")])

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                get_text("find_candidates_success", language).format(count=len(candidates)),
                reply_markup=reply_markup,
                parse_mode="HTML",
            )

        except Exception as e:
            logger.error(f"Find candidates command error: {e}")
            await update.message.reply_text(get_text("error_unknown", "ru"))

    async def pairs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /pairs"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text(get_text("error_authentication", "ru"))
                return

            language = await self._get_user_language(update)

            # Получаем пары пользователя
            pairs = await self.api_client.get_user_pairs()

            if not pairs:
                await update.message.reply_text(get_text("pairs_empty", language))
                return

            # Формируем список пар
            pairs_text = get_text("pairs_welcome", language) + "\n\n"
            for i, pair in enumerate(pairs[:5], 1):  # Ограничиваем количество
                partner_name = pair.get("partner_name", "Пользователь")
                status = pair.get("status", "unknown")
                created_at = pair.get("created_at", "")

                status_emoji = "✅" if status == "confirmed" else "⏳" if status == "pending" else "❌"
                pairs_text += f"{i}. {status_emoji} {partner_name} ({status})\n"

            await update.message.reply_text(pairs_text, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Pairs command error: {e}")
            await update.message.reply_text(get_text("error_unknown", "ru"))

    async def feedback_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /feedback"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text(get_text("error_authentication", "ru"))
                return

            language = await self._get_user_language(update)

            # Создаем кнопки для обратной связи
            keyboard = [
                [
                    InlineKeyboardButton("📥 Полученная", callback_data="feedback_received"),
                    InlineKeyboardButton("📤 Данная", callback_data="feedback_given"),
                ],
                [
                    InlineKeyboardButton(get_button_text("cancel", language), callback_data="cancel"),
                ],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                get_text("feedback_welcome", language), reply_markup=reply_markup, parse_mode="HTML"
            )

        except Exception as e:
            logger.error(f"Feedback command error: {e}")
            await update.message.reply_text(get_text("error_unknown", "ru"))

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /stats"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text(get_text("error_authentication", "ru"))
                return

            language = await self._get_user_language(update)

            # Получаем статистику пользователя
            stats = await self.api_client.get_user_stats()

            stats_text = get_text("stats_format", language).format(
                total_sessions=stats.get("total_sessions", 0),
                feedback_count=stats.get("feedback_count", 0),
                total_registrations=stats.get("total_registrations", 0),
                total_pairs=stats.get("total_pairs", 0),
                confirmed_pairs=stats.get("confirmed_pairs", 0),
            )

            await update.message.reply_text(stats_text, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Stats command error: {e}")
            await update.message.reply_text(get_text("error_unknown", "ru"))

    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /profile"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text(get_text("error_authentication", "ru"))
                return

            language = await self._get_user_language(update)

            # Получаем профиль пользователя
            profile = await self.api_client.get_user_profile()

            profile_text = get_text("profile_welcome", language) + "\n\n"
            profile_text += f"👤 Имя: {profile.get('first_name', 'Не указано')}\n"
            profile_text += f"📧 Email: {profile.get('email', 'Не указан')}\n"
            profile_text += f"🎯 Пол: {profile.get('gender', 'Не указан')}\n"
            profile_text += f"📅 Создан: {profile.get('created_at', 'Не указано')}"

            await update.message.reply_text(profile_text, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Profile command error: {e}")
            await update.message.reply_text(get_text("error_unknown", "ru"))

    async def cancel_registration_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /cancel"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text(get_text("error_authentication", "ru"))
                return

            language = await self._get_user_language(update)

            # Отменяем регистрацию
            result = await self.api_client.cancel_registration()

            await update.message.reply_text(get_text("registration_cancelled", language))

        except Exception as e:
            logger.error(f"Cancel registration command error: {e}")
            await update.message.reply_text(get_text("error_unknown", "ru"))

    async def quick_language_en(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Быстрое переключение на английский"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text(get_text("error_authentication", "en"))
                return

            # Обновляем настройки языка
            await self.api_client.update_user_settings({"language": "en"})
            await update.message.reply_text(get_text("language_changed", "en"))

        except Exception as e:
            logger.error(f"Language change error: {e}")
            await update.message.reply_text(get_text("error_unknown", "en"))

    async def quick_language_ru(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Быстрое переключение на русский"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text(get_text("error_authentication", "ru"))
                return

            # Обновляем настройки языка
            await self.api_client.update_user_settings({"language": "ru"})
            await update.message.reply_text(get_text("language_changed", "ru"))

        except Exception as e:
            logger.error(f"Language change error: {e}")
            await update.message.reply_text(get_text("error_unknown", "ru"))

    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений"""
        try:
            if not await self._authenticate_user(update):
                await update.message.reply_text(get_text("error_authentication", "ru"))
                return

            # Пока просто отвечаем стандартным сообщением
            await update.message.reply_text("Используйте команды бота для навигации. Нажмите /help для справки.")

        except Exception as e:
            logger.error(f"Text message handler error: {e}")
            await update.message.reply_text(get_text("error_unknown", "ru"))
