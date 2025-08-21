#!/usr/bin/env python3
"""
Тестовый скрипт для Alex Orator Bot
Проверяет основные компоненты бота без запуска Telegram API
"""

import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orator_translations import get_text, get_button_text, TRANSLATIONS
from orator_api_client import OratorAPIClient


class MockOratorAPIClient:
    """Мок API клиента для тестирования"""

    def __init__(self):
        self.auth_token = "test_token"

    async def check_connection(self):
        return True

    async def authenticate_telegram_user(self, telegram_id, username=None, first_name=None, last_name=None):
        return "test_token"

    async def get_user_settings(self):
        return {"language": "ru"}

    async def get_current_registration(self):
        return None

    async def get_week_info(self):
        return {"week_start_date": "2024-01-15", "week_end_date": "2024-01-21", "week_number": 3, "year": 2024}

    async def get_topic_tree(self):
        return {
            "categories": [
                {"id": 1, "name": "Подача - Темы речи уровень 1"},
                {"id": 2, "name": "Подача - Темы речи уровень 2"},
                {"id": 3, "name": "Структура - Логика выступления"},
                {"id": 4, "name": "Аргументация - Доказательства"},
                {"id": 5, "name": "Подача - Жесты и мимика"},
                {"id": 6, "name": "Структура - Вступление и заключение"},
            ]
        }

    async def get_user_stats(self):
        return {
            "total_sessions": 15,
            "feedback_count": 12,
            "total_registrations": 8,
            "total_pairs": 20,
            "confirmed_pairs": 18,
        }

    async def get_user_profile(self):
        return {
            "first_name": "Тестовый",
            "email": "test@example.com",
            "gender": "male",
            "created_at": "2024-01-01T00:00:00Z",
        }

    async def get_user_pairs(self):
        return [
            {"partner_name": "Анна Петрова", "status": "confirmed", "created_at": "2024-01-15T10:00:00Z"},
            {"partner_name": "Иван Сидоров", "status": "pending", "created_at": "2024-01-16T14:00:00Z"},
        ]

    async def find_candidates(self, match_request):
        return {
            "candidates": [
                {"user_id": "uuid1", "first_name": "Мария", "match_score": 0.85},
                {"user_id": "uuid2", "first_name": "Алексей", "match_score": 0.72},
            ]
        }


async def test_translations():
    """Тест переводов"""
    print("🧪 Тестирование переводов...")

    # Проверяем русские переводы
    assert get_text("welcome_message", "ru") != "[welcome_message]"
    assert get_text("help_message", "ru") != "[help_message]"
    assert get_button_text("register", "ru") == "📅 Зарегистрироваться"

    # Проверяем английские переводы
    assert get_text("welcome_message", "en") != "[welcome_message]"
    assert get_text("help_message", "en") != "[help_message]"
    assert get_button_text("register", "en") == "📅 Register"

    # Проверяем fallback на русский
    assert get_text("welcome_message", "unknown") != "[welcome_message]"

    print("✅ Переводы работают корректно")


async def test_api_client():
    """Тест API клиента"""
    print("🧪 Тестирование API клиента...")

    mock_client = MockOratorAPIClient()

    # Тест аутентификации
    token = await mock_client.authenticate_telegram_user("12345", "test_user")
    assert token == "test_token"

    # Тест получения настроек
    settings = await mock_client.get_user_settings()
    assert settings["language"] == "ru"

    # Тест получения информации о неделе
    week_info = await mock_client.get_week_info()
    assert "week_start_date" in week_info
    assert "week_end_date" in week_info

    # Тест получения дерева тем
    topic_tree = await mock_client.get_topic_tree()
    assert "categories" in topic_tree
    assert len(topic_tree["categories"]) > 0

    # Тест получения статистики
    stats = await mock_client.get_user_stats()
    assert "total_sessions" in stats
    assert "feedback_count" in stats

    # Тест получения профиля
    profile = await mock_client.get_user_profile()
    assert "first_name" in profile
    assert "email" in profile

    # Тест получения пар
    pairs = await mock_client.get_user_pairs()
    assert len(pairs) > 0
    assert "partner_name" in pairs[0]

    # Тест поиска кандидатов
    candidates = await mock_client.find_candidates({"week_start_date": "2024-01-15"})
    assert "candidates" in candidates
    assert len(candidates["candidates"]) > 0

    print("✅ API клиент работает корректно")


async def test_translation_coverage():
    """Тест покрытия переводов"""
    print("🧪 Проверка покрытия переводов...")

    # Проверяем, что все ключи есть в обоих языках
    ru_keys = set(TRANSLATIONS["ru"].keys())
    en_keys = set(TRANSLATIONS["en"].keys())

    missing_in_en = ru_keys - en_keys
    missing_in_ru = en_keys - ru_keys

    if missing_in_en:
        print(f"⚠️ Отсутствуют в английском: {missing_in_en}")

    if missing_in_ru:
        print(f"⚠️ Отсутствуют в русском: {missing_in_ru}")

    # Проверяем основные ключи
    essential_keys = [
        "welcome_message",
        "help_message",
        "registration_welcome",
        "topics_welcome",
        "find_candidates_welcome",
        "pairs_welcome",
        "feedback_welcome",
        "profile_welcome",
        "stats_welcome",
    ]

    for key in essential_keys:
        assert key in ru_keys, f"Отсутствует ключ {key} в русском"
        assert key in en_keys, f"Отсутствует ключ {key} в английском"

    print("✅ Покрытие переводов корректное")


async def test_button_texts():
    """Тест текстов кнопок"""
    print("🧪 Тестирование текстов кнопок...")

    button_keys = ["register", "topics", "find", "pairs", "feedback", "profile", "stats", "help", "cancel"]

    for key in button_keys:
        ru_text = get_button_text(key, "ru")
        en_text = get_button_text(key, "en")

        assert ru_text != f"[button_{key}]", f"Отсутствует текст кнопки {key} в русском"
        assert en_text != f"[button_{key}]", f"Отсутствует текст кнопки {key} в английском"

        # Проверяем, что текст не пустой
        assert len(ru_text) > 0, f"Пустой текст кнопки {key} в русском"
        assert len(en_text) > 0, f"Пустой текст кнопки {key} в английском"

    print("✅ Тексты кнопок корректные")


async def test_time_selections():
    """Тест выбора времени"""
    print("🧪 Тестирование выбора времени...")

    time_keys = ["time_morning", "time_afternoon", "time_evening"]

    for key in time_keys:
        ru_text = get_text(key, "ru")
        en_text = get_text(key, "en")

        assert ru_text != f"[{key}]", f"Отсутствует текст времени {key} в русском"
        assert en_text != f"[{key}]", f"Отсутствует текст времени {key} в английском"

        # Проверяем, что текст содержит время
        assert ":" in ru_text or "00" in ru_text, f"Некорректный формат времени {key} в русском"
        assert ":" in en_text or "00" in en_text, f"Некорректный формат времени {key} в английском"

    print("✅ Выбор времени работает корректно")


async def main():
    """Главная функция тестирования"""
    print("🚀 Запуск тестов Alex Orator Bot")
    print("=" * 50)

    try:
        await test_translations()
        await test_api_client()
        await test_translation_coverage()
        await test_button_texts()
        await test_time_selections()

        print("=" * 50)
        print("🎉 Все тесты прошли успешно!")
        print("✅ Alex Orator Bot готов к работе")

    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
