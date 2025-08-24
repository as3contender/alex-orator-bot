#!/usr/bin/env python3
"""
Скрипт для тестирования импортов в Docker контейнере
"""

import os
import sys

print("🔍 Тестирование импортов в Docker...")
print(f"📁 Текущая директория: {os.getcwd()}")
print(f"📁 Содержимое директории: {os.listdir('.')}")

# Добавляем путь к корневой директории admin-panel
current_dir = os.path.dirname(os.path.abspath(__file__))
admin_panel_root = current_dir
sys.path.append(admin_panel_root)

print(f"📁 Путь к admin-panel: {admin_panel_root}")
print(f"📁 Python path: {sys.path}")

try:
    print("🔧 Тестирование импорта security.auth...")
    from security.auth import get_auth, auth

    print("✅ security.auth импортирован успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта security.auth: {e}")

try:
    print("🔧 Тестирование импорта database.database...")
    from database.database import get_db, db

    print("✅ database.database импортирован успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта database.database: {e}")

try:
    print("🔧 Тестирование импорта security.security...")
    from security.security import get_security_manager

    print("✅ security.security импортирован успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта security.security: {e}")

print("🎯 Тестирование завершено!")
