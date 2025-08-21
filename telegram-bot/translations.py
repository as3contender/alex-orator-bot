# Словарь переводов
TRANSLATIONS = {
    "ru": {
        "welcome_message": "Привет, {name}! 👋\n\nЯ - интеллектуальный бот для анализа данных. Можешь задавать мне вопросы на естественном языке, и я найду нужную информацию в базе данных.\n\nПопробуй один из примеров ниже или задай свой вопрос:",
        "help_message": """📚 <b>Справка по использованию бота:</b>

<b>Основные команды:</b>
/start - Начать работу с ботом
/help - Показать эту справку
/tables - Список доступных таблиц
/sample - Примеры данных из таблиц
/settings - Настройки пользователя

<b>Быстрые команды:</b>
/en - Переключить на английский
/ru - Переключить на русский

<b>Примеры запросов:</b>
• "Покажи топ 10 клиентов"
• "Сколько заказов было в этом месяце?"
• "Средняя сумма заказа по регионам"
• "Количество новых пользователей за последние 30 дней"

<b>Настройки:</b>
В разделе /settings можно настроить:
• Язык интерфейса
• Показ объяснений SQL
• Показ SQL запросов
• Максимальное количество результатов""",
        "no_tables": "Нет доступных таблиц в базе данных",
        "select_table_for_sample": "Выберите таблицу для просмотра примера данных:",
        "query_error": "Произошла ошибка при обработке запроса. Попробуйте переформулировать вопрос.",
        "sample_query_1": "📊 Топ клиенты",
        "sample_query_2": "💰 Продажи",
        "sample_query_3": "👥 Пользователи",
        "sample_query_4": "📈 Статистика",
        "sample_query_1_text": "Покажи топ 10 клиентов по сумме заказов",
        "sample_query_2_text": "Покажи продажи за последний месяц",
        "sample_query_3_text": "Сколько новых пользователей зарегистрировалось в этом году",
        "sample_query_4_text": "Средняя сумма заказа по месяцам",
        "help_button": "❓ Справка",
        "tables_button": "📊 Таблицы",
        "toggle_explanations": "💡 Объяснения",
        "toggle_sql": "🔍 SQL",
        "change_language": "🌐 Язык",
        "reset_settings": "🔄 Сброс",
    },
    "en": {
        "welcome_message": "Hello, {name}! 👋\n\nI'm an intelligent data analysis bot. You can ask me questions in natural language, and I'll find the information you need in the database.\n\nTry one of the examples below or ask your own question:",
        "help_message": """📚 <b>Bot usage guide:</b>

<b>Main commands:</b>
/start - Start working with the bot
/help - Show this help
/tables - List of available tables
/sample - Sample data from tables
/settings - User settings

<b>Quick commands:</b>
/en - Switch to English
/ru - Switch to Russian

<b>Query examples:</b>
• "Show top 10 customers"
• "How many orders were there this month?"
• "Average order amount by region"
• "Number of new users in the last 30 days"

<b>Settings:</b>
In /settings you can configure:
• Interface language
• Show SQL explanations
• Show SQL queries
• Maximum number of results""",
        "no_tables": "No tables available in the database",
        "select_table_for_sample": "Select a table to view sample data:",
        "query_error": "An error occurred while processing the query. Try rephrasing your question.",
        "sample_query_1": "📊 Top customers",
        "sample_query_2": "💰 Sales",
        "sample_query_3": "👥 Users",
        "sample_query_4": "📈 Statistics",
        "sample_query_1_text": "Show top 10 customers by order amount",
        "sample_query_2_text": "Show sales for the last month",
        "sample_query_3_text": "How many new users registered this year",
        "sample_query_4_text": "Average order amount by month",
        "help_button": "❓ Help",
        "tables_button": "📊 Tables",
        "toggle_explanations": "💡 Explanations",
        "toggle_sql": "🔍 SQL",
        "change_language": "🌐 Language",
        "reset_settings": "🔄 Reset",
    },
}


def get_text(key: str, language: str = "ru") -> str:
    """Получение перевода по ключу и языку"""
    if language not in TRANSLATIONS:
        language = "ru"  # Fallback to Russian

    return TRANSLATIONS[language].get(key, f"[{key}]")
