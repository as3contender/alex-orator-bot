#!/usr/bin/env python3
"""
Скрипт для применения изменений в базе данных
Запускать перед использованием админ-панели
"""

import os
import sys
import logging

# Добавляем путь к корневой директории admin-panel
current_dir = os.path.dirname(os.path.abspath(__file__))
admin_panel_root = os.path.dirname(current_dir)
sys.path.append(admin_panel_root)

try:
    from database.database import AdminDatabase
except ImportError as e:
    print(f"❌ Ошибка импорта модулей: {e}")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def apply_db_changes():
    """Применение изменений в базе данных"""
    try:
        db = AdminDatabase()
        db.connect()

        # SQL для изменения telegram_id на nullable
        sql_changes = """
        -- Изменяем поле telegram_id на nullable
        ALTER TABLE users ALTER COLUMN telegram_id DROP NOT NULL;
        
        -- Добавляем комментарий к таблице
        COMMENT ON COLUMN users.telegram_id IS 'Telegram ID пользователя. NULL для системных администраторов';
        """

        with db.conn.cursor() as cursor:
            cursor.execute(sql_changes)
            db.conn.commit()

        logger.info("✅ Изменения в базе данных успешно применены")
        logger.info("📋 Поле telegram_id теперь nullable")
        logger.info("🔧 Теперь можно создавать системных администраторов")

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка применения изменений: {e}")
        return False


def main():
    """Главная функция"""
    logger.info("🚀 Применение изменений в базе данных")

    if apply_db_changes():
        logger.info("✅ Все изменения успешно применены")
        logger.info("💡 Теперь можно запускать скрипт миграции паролей")
    else:
        logger.error("❌ Ошибка применения изменений")
        return False

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
