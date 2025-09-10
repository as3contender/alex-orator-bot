#!/usr/bin/env python3
"""
Скрипт для обновления импортов после реорганизации файлов
Запускать после перемещения файлов в новые папки
"""

import os
import re
from pathlib import Path

# Маппинг старых импортов на новые
IMPORT_MAPPING = {
    # Безопасность
    "from security.auth import": "from security.auth import",
    "import security.security as security.auth as auth": "import security.security as security.auth as auth",
    "from security.security import": "from security.security import",
    "import security.security as security": "import security.security as security.security as security",
    "from security.access_control import": "from security.access_control import",
    "import security.access_control as access_control": "import security.security as security.access_control as access_control",
    # База данных
    "from database.database import": "from database.database import",
    "import database.database as database": "import database.database as database.database as database",
    # UI (если есть прямые импорты)
    "from ui.admin_app import": "from ui.admin_app import",
    "from ui.users_management import": "from ui.users_management import",
    "from ui.content_page import": "from ui.content_page import",
    # Утилиты
    "from utils.migrate_passwords import": "from utils.migrate_passwords import",
    "import utils.migrate_passwords as migrate_passwords": "import utils.migrate_passwords as migrate_passwords",
}


def update_imports_in_file(file_path):
    """Обновить импорты в одном файле"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content

        # Применяем маппинг импортов
        for old_import, new_import in IMPORT_MAPPING.items():
            content = content.replace(old_import, new_import)

        # Если контент изменился, записываем обратно
        if content != original_content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ Обновлен: {file_path}")
            return True
        else:
            print(f"ℹ️  Без изменений: {file_path}")
            return False

    except Exception as e:
        print(f"❌ Ошибка обработки {file_path}: {e}")
        return False


def find_python_files(directory):
    """Найти все Python файлы в директории"""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Пропускаем папки с точкой в начале
        dirs[:] = [d for d in dirs if not d.startswith(".")]

        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def main():
    """Главная функция"""
    print("🔄 Начинаем обновление импортов...")

    # Получаем текущую директорию
    current_dir = Path(__file__).parent.parent
    print(f"📁 Рабочая директория: {current_dir}")

    # Находим все Python файлы
    python_files = find_python_files(current_dir)
    print(f"📄 Найдено {len(python_files)} Python файлов")

    # Обновляем импорты в каждом файле
    updated_count = 0
    for file_path in python_files:
        if update_imports_in_file(file_path):
            updated_count += 1

    print(f"\n✅ Обновление завершено!")
    print(f"📊 Обновлено файлов: {updated_count}")
    print(f"📊 Всего файлов: {len(python_files)}")

    if updated_count > 0:
        print("\n⚠️  ВАЖНО: Проверьте обновленные файлы на корректность импортов!")
        print("💡 Рекомендуется запустить тесты для проверки работоспособности.")


if __name__ == "__main__":
    main()
