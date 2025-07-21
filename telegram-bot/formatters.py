from typing import List, Dict, Any
from config import MAX_MESSAGE_LENGTH, MAX_RESULTS_DISPLAY


def format_tables_list(tables: List[Any], language: str) -> str:
    """Форматирование списка таблиц"""
    if language == "ru":
        header = "📊 <b>Доступные таблицы:</b>\n\n"
        no_tables = "Нет доступных таблиц"
    else:
        header = "📊 <b>Available tables:</b>\n\n"
        no_tables = "No tables available"

    if not tables:
        return no_tables

    result = header
    for i, table in enumerate(tables, 1):
        row_count = f" ({table.row_count} строк)" if table.row_count else ""
        description = f" - {table.description}" if table.description else ""
        result += f"{i}. <code>{table.name}</code>{row_count}{description}\n"

    return result


def format_sample_data(sample_data: Any, language: str) -> str:
    """Форматирование примера данных"""
    if language == "ru":
        header = f"📋 <b>Пример данных из таблицы {sample_data.table}:</b>\n\n"
        no_data = "Нет данных для отображения"
    else:
        header = f"📋 <b>Sample data from table {sample_data.table}:</b>\n\n"
        no_data = "No data to display"

    if not sample_data.data:
        return no_data

    result = header

    # Получаем заголовки колонок
    if sample_data.data:
        columns = list(sample_data.data[0].keys())
        result += "| " + " | ".join(columns) + " |\n"
        result += "|" + "|".join(["---"] * len(columns)) + "|\n"

        # Добавляем данные (ограничиваем количество строк)
        for row in sample_data.data[:MAX_RESULTS_DISPLAY]:
            values = [str(row.get(col, "")) for col in columns]
            result += "| " + " | ".join(values) + " |\n"

        if len(sample_data.data) > MAX_RESULTS_DISPLAY:
            result += f"\n<i>Показано {MAX_RESULTS_DISPLAY} из {len(sample_data.data)} строк</i>"

    return result


def format_query_results(
    result: Dict[str, Any], language: str, show_explanations: bool, show_sql: bool, max_results: int
) -> str:
    """Форматирование результатов запроса"""
    if language == "ru":
        header = "📊 <b>Результаты запроса:</b>\n\n"
        no_data = "Нет данных для отображения"
        explanation_header = "💡 <b>Объяснение:</b>\n"
        sql_header = "🔍 <b>SQL запрос:</b>\n"
        row_count = "строк"
    else:
        header = "📊 <b>Query results:</b>\n\n"
        no_data = "No data to display"
        explanation_header = "💡 <b>Explanation:</b>\n"
        sql_header = "🔍 <b>SQL query:</b>\n"
        row_count = "rows"

    result_text = header

    # Добавляем объяснение
    if show_explanations and result.get("explanation"):
        result_text += explanation_header + result["explanation"] + "\n\n"

    # Добавляем SQL запрос
    if show_sql and result.get("sql"):
        result_text += sql_header + f"<code>{result['sql']}</code>\n\n"

    # Добавляем данные
    data = result.get("data", [])
    if not data:
        result_text += no_data
        return result_text

    # Получаем заголовки колонок
    columns = list(data[0].keys())
    result_text += "| " + " | ".join(columns) + " |\n"
    result_text += "|" + "|".join(["---"] * len(columns)) + "|\n"

    # Добавляем данные (ограничиваем количество строк)
    display_count = min(len(data), max_results, MAX_RESULTS_DISPLAY)
    for row in data[:display_count]:
        values = [str(row.get(col, "")) for col in columns]
        result_text += "| " + " | ".join(values) + " |\n"

    # Добавляем информацию о количестве строк
    if len(data) > display_count:
        result_text += f"\n<i>Показано {display_count} из {len(data)} {row_count}</i>"
    else:
        result_text += f"\n<i>Всего {len(data)} {row_count}</i>"

    # Проверяем длину сообщения
    if len(result_text) > MAX_MESSAGE_LENGTH:
        result_text = (
            result_text[: MAX_MESSAGE_LENGTH - 100] + "...\n\n<i>Сообщение обрезано из-за ограничений Telegram</i>"
        )

    return result_text


def format_settings(settings: Any, language: str) -> str:
    """Форматирование настроек пользователя"""
    if language == "ru":
        header = "⚙️ <b>Настройки пользователя:</b>\n\n"
        language_text = "Язык интерфейса"
        explanations_text = "Показывать объяснения"
        sql_text = "Показывать SQL запросы"
        max_results_text = "Максимум результатов"
        auto_format_text = "Автоформатирование"
        enabled = "Включено"
        disabled = "Отключено"
    else:
        header = "⚙️ <b>User settings:</b>\n\n"
        language_text = "Interface language"
        explanations_text = "Show explanations"
        sql_text = "Show SQL queries"
        max_results_text = "Max results"
        auto_format_text = "Auto formatting"
        enabled = "Enabled"
        disabled = "Disabled"

    result = header
    result += f"🌐 <b>{language_text}:</b> {settings.language.upper()}\n"
    result += f"💡 <b>{explanations_text}:</b> {enabled if settings.show_explanations else disabled}\n"
    result += f"🔍 <b>{sql_text}:</b> {enabled if settings.show_sql else disabled}\n"
    result += f"📊 <b>{max_results_text}:</b> {settings.max_results}\n"
    result += f"✨ <b>{auto_format_text}:</b> {enabled if settings.auto_format else disabled}\n"

    return result
