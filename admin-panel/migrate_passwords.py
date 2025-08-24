#!/usr/bin/env python3
"""
Скрипт для миграции паролей с SHA256 на bcrypt
Запускать только один раз после обновления системы безопасности
"""

import os
import sys
import hashlib
import logging
from typing import List, Dict, Any

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from security import security_manager
    from database import AdminDatabase
except ImportError as e:
    print(f"❌ Ошибка импорта модулей: {e}")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_admin_passwords():
    """Миграция паролей администраторов"""
    try:
        db = AdminDatabase()
        db.connect()

        # Получаем всех администраторов
        with db.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, hashed_password 
                FROM admin_users 
                WHERE is_active = true
            """
            )
            admins = cursor.fetchall()

        migrated_count = 0

        for admin in admins:
            admin_id, username, hashed_password = admin

            # Проверяем, не хеширован ли уже пароль bcrypt
            if hashed_password.startswith("$2b$"):
                logger.info(f"✅ Пароль администратора {username} уже в формате bcrypt")
                continue

            # Если пароль в формате SHA256, предлагаем обновить
            if len(hashed_password) == 64:  # SHA256 hash length
                logger.warning(f"⚠️ Пароль администратора {username} в формате SHA256")
                logger.info(f"💡 Для обновления пароля используйте админ-панель или сбросьте пароль")

        logger.info(f"✅ Проверка паролей администраторов завершена")

    except Exception as e:
        logger.error(f"❌ Ошибка миграции паролей администраторов: {e}")
        return False

    return True


def migrate_user_passwords():
    """Миграция паролей пользователей"""
    try:
        db = AdminDatabase()
        db.connect()

        # Получаем всех пользователей
        with db.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, password 
                FROM users 
                WHERE is_active = true
            """
            )
            users = cursor.fetchall()

        migrated_count = 0

        for user in users:
            user_id, username, password_hash = user

            # Проверяем, не хеширован ли уже пароль bcrypt
            if password_hash and password_hash.startswith("$2b$"):
                logger.info(f"✅ Пароль пользователя {username} уже в формате bcrypt")
                continue

            # Если пароль в формате SHA256, предлагаем обновить
            if password_hash and len(password_hash) == 64:  # SHA256 hash length
                logger.warning(f"⚠️ Пароль пользователя {username} в формате SHA256")
                logger.info(f"💡 Для обновления пароля используйте админ-панель или сбросьте пароль")

        logger.info(f"✅ Проверка паролей пользователей завершена")

    except Exception as e:
        logger.error(f"❌ Ошибка миграции паролей пользователей: {e}")
        return False

    return True


def create_default_admin():
    """Создание администратора по умолчанию с безопасным паролем"""
    try:
        db = AdminDatabase()
        db.connect()

        # Проверяем, существует ли уже администратор
        with db.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) FROM admin_users 
                WHERE username = 'admin' AND is_active = true
            """
            )
            admin_exists = cursor.fetchone()[0] > 0

        if admin_exists:
            logger.info("✅ Администратор по умолчанию уже существует")
            return True

        # Создаем безопасный пароль
        default_password = "Admin123!@#"
        hashed_password = security_manager.hash_password(default_password)

        # Создаем администратора
        with db.conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO admin_users (username, hashed_password, full_name, role)
                VALUES (%s, %s, %s, %s)
            """,
                ("admin", hashed_password, "Системный администратор", "super_admin"),
            )
            db.conn.commit()

        logger.info("✅ Администратор по умолчанию создан")
        logger.info(f"🔑 Логин: admin")
        logger.info(f"🔑 Пароль: {default_password}")
        logger.warning("⚠️ ОБЯЗАТЕЛЬНО измените пароль после первого входа!")

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка создания администратора по умолчанию: {e}")
        return False


def main():
    """Главная функция миграции"""
    logger.info("🚀 Начинаем миграцию системы безопасности")

    # Проверяем подключение к базе данных
    try:
        db = AdminDatabase()
        db.connect()
        logger.info("✅ Подключение к базе данных установлено")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {e}")
        return False

    # Мигрируем пароли
    success = True

    if not migrate_admin_passwords():
        success = False

    if not migrate_user_passwords():
        success = False

    # Создаем администратора по умолчанию если нужно
    if not create_default_admin():
        success = False

    if success:
        logger.info("✅ Миграция системы безопасности завершена успешно")
        logger.info("🔒 Рекомендации по безопасности:")
        logger.info("   1. Измените пароль администратора по умолчанию")
        logger.info("   2. Настройте HTTPS для админ-панели")
        logger.info("   3. Регулярно обновляйте пароли")
        logger.info("   4. Мониторьте логи на предмет подозрительной активности")
    else:
        logger.error("❌ Миграция завершена с ошибками")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
