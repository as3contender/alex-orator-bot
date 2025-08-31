#!/usr/bin/env python3
"""
Тестовый файл для проверки импортов
"""


def test_imports():
    """Тестируем импорты"""
    try:
        print("🔍 Тестируем импорты...")

        # Тест импорта database
        print("📦 Импортируем database...")
        from database.database import get_db

        print("✅ database импортирован успешно")

        # Тест импорта topics_and_tasks_page
        print("📦 Импортируем topics_and_tasks_page...")
        from ui.topics_and_tasks_page import topics_and_tasks_management_page

        print("✅ topics_and_tasks_page импортирован успешно")

        # Тест импорта content_page
        print("📦 Импортируем content_page...")
        from ui.content_page import content_management_page

        print("✅ content_page импортирован успешно")

        # Тест импорта users_management
        print("📦 Импортируем users_management...")
        from ui.users_management import users_management_page

        print("✅ users_management импортирован успешно")

        print("🎉 Все импорты работают корректно!")
        return True

    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False


if __name__ == "__main__":
    test_imports()
