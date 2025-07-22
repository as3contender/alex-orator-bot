"""
Переводы для Alex Orator Bot
"""

TRANSLATIONS = {
    "ru": {
        # Приветствие и помощь
        "welcome_message": """🎤 <b>Добро пожаловать в Alex Orator Bot!</b>

Я помогу вам найти партнера для тренировки ораторского искусства.

<b>Основные команды:</b>
/register - Зарегистрироваться на неделю
/topics - Выбрать темы для тренировки
/find - Найти кандидатов
/pairs - Мои пары
/feedback - Обратная связь
/profile - Мой профиль
/stats - Статистика
/help - Помощь

Начните с регистрации на неделю! 📅""",
        "help_message": """📚 <b>Справка по командам Alex Orator Bot</b>

<b>Основные команды:</b>
• /start - Запуск бота
• /help - Эта справка
• /register - Зарегистрироваться на неделю
• /topics - Выбрать темы для тренировки
• /find - Найти кандидатов для пары
• /pairs - Просмотр моих пар
• /feedback - Обратная связь
• /profile - Мой профиль
• /stats - Статистика
• /cancel - Отменить регистрацию

<b>Быстрые команды:</b>
• /en - Переключить на английский
• /ru - Переключить на русский

<b>Как это работает:</b>
1. Зарегистрируйтесь на неделю (/register)
2. Выберите темы для тренировки (/topics)
3. Найдите кандидатов (/find)
4. Создайте пару и тренируйтесь
5. Оставьте обратную связь (/feedback)""",
        # Регистрация
        "registration_welcome": "📅 <b>Регистрация на неделю</b>\n\nВыберите предпочтительное время для тренировок:",
        "registration_success": "✅ <b>Регистрация успешна!</b>\n\nТеперь выберите темы для тренировки:",
        "registration_already_exists": "⚠️ У вас уже есть активная регистрация на эту неделю.",
        "registration_cancelled": "❌ Регистрация отменена.",
        "registration_failed": "❌ Ошибка при регистрации. Попробуйте позже.",
        # Темы
        "topics_welcome": "🎯 <b>Выбор тем для тренировки</b>\n\nВыберите темы, которые хотите тренировать:",
        "topics_selected": "✅ <b>Темы выбраны!</b>\n\nТеперь можете найти кандидатов для пары.",
        "topics_failed": "❌ Ошибка при выборе тем. Попробуйте позже.",
        # Поиск кандидатов
        "find_candidates_welcome": "🔍 <b>Поиск кандидатов</b>\n\nИщу подходящих партнеров для тренировки...",
        "find_candidates_success": "✅ <b>Найдено кандидатов: {count}</b>\n\nВыберите партнера:",
        "find_candidates_no_results": "😔 <b>Кандидаты не найдены</b>\n\nПопробуйте позже или измените критерии поиска.",
        "find_candidates_failed": "❌ Ошибка при поиске кандидатов. Попробуйте позже.",
        # Пары
        "pairs_welcome": "👥 <b>Мои пары</b>\n\nВаши текущие и прошлые пары:",
        "pairs_empty": "📭 У вас пока нет пар.\n\nИспользуйте /find для поиска партнеров.",
        "pair_created": "✅ <b>Пара создана!</b>\n\nОжидайте подтверждения от партнера.",
        "pair_confirmed": "✅ <b>Пара подтверждена!</b>\n\nМожете начинать тренировку.",
        "pair_failed": "❌ Ошибка при создании пары. Попробуйте позже.",
        # Обратная связь
        "feedback_welcome": "💬 <b>Обратная связь</b>\n\nВыберите пару для оставления отзыва:",
        "feedback_received": "📥 <b>Полученная обратная связь</b>\n\nОтзывы о ваших выступлениях:",
        "feedback_given": "📤 <b>Данная обратная связь</b>\n\nВаши отзывы о партнерах:",
        "feedback_empty": "📭 Пока нет обратной связи.",
        "feedback_created": "✅ <b>Обратная связь отправлена!</b>\n\nСпасибо за ваш отзыв.",
        # Профиль
        "profile_welcome": "👤 <b>Мой профиль</b>\n\nИнформация о вашем профиле:",
        "profile_updated": "✅ <b>Профиль обновлен!</b>",
        "profile_failed": "❌ Ошибка при обновлении профиля.",
        # Статистика
        "stats_welcome": "📊 <b>Моя статистика</b>\n\nВаши достижения:",
        "stats_format": """📈 <b>Статистика тренировок</b>

🎯 Всего сессий: {total_sessions}
💬 Обратной связи: {feedback_count}
📅 Регистраций: {total_registrations}
👥 Созданных пар: {total_pairs}
✅ Подтвержденных пар: {confirmed_pairs}""",
        # Кнопки
        "button_register": "📅 Зарегистрироваться",
        "button_topics": "🎯 Выбрать темы",
        "button_find": "🔍 Найти кандидатов",
        "button_pairs": "👥 Мои пары",
        "button_feedback": "💬 Обратная связь",
        "button_profile": "👤 Профиль",
        "button_stats": "📊 Статистика",
        "button_help": "❓ Помощь",
        "button_cancel": "❌ Отменить",
        "button_confirm": "✅ Подтвердить",
        "button_back": "⬅️ Назад",
        "button_next": "➡️ Далее",
        # Время
        "time_morning": "🌅 Утро (9:00-12:00)",
        "time_afternoon": "☀️ День (12:00-18:00)",
        "time_evening": "🌆 Вечер (18:00-22:00)",
        # Ошибки
        "error_authentication": "❌ Ошибка аутентификации. Попробуйте /start",
        "error_backend": "❌ Ошибка соединения с сервером. Попробуйте позже.",
        "error_unknown": "❌ Произошла неизвестная ошибка. Попробуйте позже.",
        # Уведомления
        "notification_new_pair": "🎉 <b>Новая пара!</b>\n\nВам предложили создать пару. Используйте /pairs для просмотра.",
        "notification_pair_confirmed": "✅ <b>Пара подтверждена!</b>\n\nМожете начинать тренировку.",
        "notification_reminder": "⏰ <b>Напоминание!</b>\n\nНе забудьте оставить обратную связь после тренировки.",
        # Язык
        "language_changed": "🌐 Язык изменен на русский.",
    },
    "en": {
        # Welcome and help
        "welcome_message": """🎤 <b>Welcome to Alex Orator Bot!</b>

I'll help you find a partner for public speaking practice.

<b>Main commands:</b>
/register - Register for the week
/topics - Choose training topics
/find - Find candidates
/pairs - My pairs
/feedback - Feedback
/profile - My profile
/stats - Statistics
/help - Help

Start by registering for the week! 📅""",
        "help_message": """📚 <b>Alex Orator Bot Commands Help</b>

<b>Main commands:</b>
• /start - Start the bot
• /help - This help
• /register - Register for the week
• /topics - Choose training topics
• /find - Find pair candidates
• /pairs - View my pairs
• /feedback - Feedback
• /profile - My profile
• /stats - Statistics
• /cancel - Cancel registration

<b>Quick commands:</b>
• /en - Switch to English
• /ru - Switch to Russian

<b>How it works:</b>
1. Register for the week (/register)
2. Choose training topics (/topics)
3. Find candidates (/find)
4. Create a pair and practice
5. Leave feedback (/feedback)""",
        # Registration
        "registration_welcome": "📅 <b>Week Registration</b>\n\nChoose your preferred training time:",
        "registration_success": "✅ <b>Registration successful!</b>\n\nNow choose training topics:",
        "registration_already_exists": "⚠️ You already have an active registration for this week.",
        "registration_cancelled": "❌ Registration cancelled.",
        "registration_failed": "❌ Registration error. Try again later.",
        # Topics
        "topics_welcome": "🎯 <b>Choose Training Topics</b>\n\nSelect topics you want to practice:",
        "topics_selected": "✅ <b>Topics selected!</b>\n\nNow you can find pair candidates.",
        "topics_failed": "❌ Error selecting topics. Try again later.",
        # Find candidates
        "find_candidates_welcome": "🔍 <b>Finding Candidates</b>\n\nLooking for suitable training partners...",
        "find_candidates_success": "✅ <b>Found candidates: {count}</b>\n\nChoose a partner:",
        "find_candidates_no_results": "😔 <b>No candidates found</b>\n\nTry again later or change search criteria.",
        "find_candidates_failed": "❌ Error finding candidates. Try again later.",
        # Pairs
        "pairs_welcome": "👥 <b>My Pairs</b>\n\nYour current and past pairs:",
        "pairs_empty": "📭 You don't have any pairs yet.\n\nUse /find to find partners.",
        "pair_created": "✅ <b>Pair created!</b>\n\nWait for partner confirmation.",
        "pair_confirmed": "✅ <b>Pair confirmed!</b>\n\nYou can start training.",
        "pair_failed": "❌ Error creating pair. Try again later.",
        # Feedback
        "feedback_welcome": "💬 <b>Feedback</b>\n\nChoose a pair to leave feedback:",
        "feedback_received": "📥 <b>Received Feedback</b>\n\nFeedback about your performances:",
        "feedback_given": "📤 <b>Given Feedback</b>\n\nYour feedback about partners:",
        "feedback_empty": "📭 No feedback yet.",
        "feedback_created": "✅ <b>Feedback sent!</b>\n\nThank you for your feedback.",
        # Profile
        "profile_welcome": "👤 <b>My Profile</b>\n\nYour profile information:",
        "profile_updated": "✅ <b>Profile updated!</b>",
        "profile_failed": "❌ Error updating profile.",
        # Statistics
        "stats_welcome": "📊 <b>My Statistics</b>\n\nYour achievements:",
        "stats_format": """📈 <b>Training Statistics</b>

🎯 Total sessions: {total_sessions}
💬 Feedback given: {feedback_count}
📅 Registrations: {total_registrations}
👥 Pairs created: {total_pairs}
✅ Confirmed pairs: {confirmed_pairs}""",
        # Buttons
        "button_register": "📅 Register",
        "button_topics": "🎯 Choose Topics",
        "button_find": "🔍 Find Candidates",
        "button_pairs": "👥 My Pairs",
        "button_feedback": "💬 Feedback",
        "button_profile": "👤 Profile",
        "button_stats": "📊 Statistics",
        "button_help": "❓ Help",
        "button_cancel": "❌ Cancel",
        "button_confirm": "✅ Confirm",
        "button_back": "⬅️ Back",
        "button_next": "➡️ Next",
        # Time
        "time_morning": "🌅 Morning (9:00-12:00)",
        "time_afternoon": "☀️ Afternoon (12:00-18:00)",
        "time_evening": "🌆 Evening (18:00-22:00)",
        # Errors
        "error_authentication": "❌ Authentication error. Try /start",
        "error_backend": "❌ Server connection error. Try again later.",
        "error_unknown": "❌ Unknown error occurred. Try again later.",
        # Notifications
        "notification_new_pair": "🎉 <b>New pair!</b>\n\nYou've been offered to create a pair. Use /pairs to view.",
        "notification_pair_confirmed": "✅ <b>Pair confirmed!</b>\n\nYou can start training.",
        "notification_reminder": "⏰ <b>Reminder!</b>\n\nDon't forget to leave feedback after training.",
        # Language
        "language_changed": "🌐 Language changed to English.",
    },
}


def get_text(key: str, language: str = "ru") -> str:
    """Получить текст по ключу и языку"""
    return TRANSLATIONS.get(language, TRANSLATIONS["ru"]).get(key, f"[{key}]")


def get_button_text(key: str, language: str = "ru") -> str:
    """Получить текст кнопки по ключу и языку"""
    return get_text(f"button_{key}", language)
