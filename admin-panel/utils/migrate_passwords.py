#!/usr/bin/env python3
"""
Скрипт для миграции паролей с SHA256 на bcrypt
Запускать только один раз после обновления системы безопасности

Использование:
    python utils/migrate_passwords.py                    # Без создания админа
    python utils/migrate_passwords.py --create-admin     # Создать админа с запросом пароля
    python utils/migrate_passwords.py --admin-password "MySecurePass123!"  # Создать админа с указанным паролем
"""

import os
import sys
import hashlib
import logging
import argparse
import getpass
from typing import List, Dict, Any

# Добавляем путь к корневой директории admin-panel
current_dir = os.path.dirname(os.path.abspath(__file__))
admin_panel_root = os.path.dirname(current_dir)  # Поднимаемся на уровень выше (из utils/ в admin-panel/)
sys.path.append(admin_panel_root)

try:
    from security.security import get_security_manager
    from database.database import AdminDatabase
except ImportError as e:
    print(f"❌ Ошибка импорта модулей: {e}")
    print(f"📁 Текущая директория: {os.getcwd()}")
    print(f"📁 Путь к admin-panel: {admin_panel_root}")
    print(f"📁 Python path: {sys.path}")
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
                FROM users 
                WHERE is_active = true
                and telegram_id IS NULL
            """
            )
            admins = cursor.fetchall()

        migrated_count = 0

        for admin in admins:
            admin_id, username, hashed_password = admin

            # Проверяем, что пароль не None
            if not hashed_password:
                logger.warning(f"⚠️ У администратора {username} отсутствует пароль")
                continue

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
                SELECT id, username, hashed_password 
                FROM users 
                WHERE is_active = true
                and telegram_id IS NULL
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


def create_default_admin(admin_password=None, force_create=False):
    """Создание администратора по умолчанию с безопасным паролем"""
    try:
        db = AdminDatabase()
        db.connect()

        # Проверяем, существует ли уже администратор
        with db.conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) FROM users 
                WHERE username = 'admin' AND is_active = true AND telegram_id IS NULL
            """
            )
            admin_exists = cursor.fetchone()[0] > 0

        if admin_exists:
            logger.info("✅ Администратор по умолчанию уже существует")
            return True

        # Если пароль не передан и не принудительное создание, спрашиваем пользователя
        if not admin_password and not force_create:
            print("❓ Хотите создать администратора по умолчанию? (y/n): ", end="")
            response = input().strip().lower()

            if response not in ["y", "yes", "да", "д"]:
                logger.info("⏭️ Создание администратора пропущено")
                logger.info("💡 Для создания администратора позже используйте админ-панель")
                return True

        # Если пароль не передан, запрашиваем его
        if not admin_password:
            print("🔐 Введите пароль для администратора (минимум 8 символов):")
            admin_password = getpass.getpass("Пароль: ")

            # Проверяем сложность пароля
            if len(admin_password) < 8:
                logger.error("❌ Пароль должен содержать минимум 8 символов")
                return False

            # Повторный ввод для подтверждения
            confirm_password = getpass.getpass("Подтвердите пароль: ")
            if admin_password != confirm_password:
                logger.error("❌ Пароли не совпадают")
                return False

                # Получаем экземпляр security_manager
        sec_manager = get_security_manager()

        # Проверяем сложность пароля
        is_valid, error_msg = sec_manager.validate_password_strength(admin_password)
        if not is_valid:
            logger.error(f"❌ Пароль не соответствует требованиям безопасности: {error_msg}")
            logger.error("💡 Пароль должен содержать: заглавные, строчные буквы, цифры, спецсимволы")
            return False

        # Хешируем пароль
        hashed_password = sec_manager.hash_password(admin_password)

        # Создаем администратора
        with db.conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (username, hashed_password, telegram_id)
                VALUES (%s, %s, %s)
            """,
                ("admin", hashed_password, None),  # NULL для системных администраторов
            )
            db.conn.commit()

        logger.info("✅ Администратор по умолчанию создан")
        logger.info(f"🔑 Логин: admin")
        if not admin_password.startswith("*"):  # Не показываем пароль, если он передан как аргумент
            logger.info(f"🔑 Пароль: {admin_password}")
        logger.warning("⚠️ ОБЯЗАТЕЛЬНО измените пароль после первого входа!")

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка создания администратора по умолчанию: {e}")
        return False


def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description="Скрипт миграции паролей и создания администратора",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python utils/migrate_passwords.py                    # Только миграция паролей
  python utils/migrate_passwords.py --create-admin     # Создать админа с запросом пароля
  python utils/migrate_passwords.py --admin-password "MySecurePass123!"  # Создать админа с указанным паролем
        """,
    )

    parser.add_argument("--create-admin", action="store_true", help="Создать администратора с запросом пароля")

    parser.add_argument(
        "--admin-password",
        type=str,
        help="Пароль для создания администратора (небезопасно передавать в командной строке)",
    )

    parser.add_argument(
        "--skip-migration", action="store_true", help="Пропустить миграцию паролей, только создать администратора"
    )

    return parser.parse_args()


def main():
    """Главная функция миграции"""
    args = parse_arguments()

    logger.info("🚀 Начинаем миграцию системы безопасности")

    # Проверяем подключение к базе данных
    try:
        db = AdminDatabase()
        db.connect()
        logger.info("✅ Подключение к базе данных установлено")
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {e}")
        return False

    # Мигрируем пароли (если не пропущено)
    success = True

    if not args.skip_migration:
        if not migrate_admin_passwords():
            success = False

        if not migrate_user_passwords():
            success = False
    else:
        logger.info("⏭️ Миграция паролей пропущена")

    # Создаем администратора (если запрошено)
    if args.create_admin or args.admin_password:
        logger.info("🔧 Создание администратора...")
        if not create_default_admin(admin_password=args.admin_password, force_create=True):
            success = False
    else:
        # Предлагаем создать администратора по умолчанию
        logger.info("🔧 Хотите создать администратора по умолчанию?")
        logger.info("   Это можно сделать позже через админ-панель")
        if not create_default_admin():
            success = False

    if success:
        logger.info("✅ Миграция системы безопасности завершена успешно")
        logger.info("🔒 Рекомендации по безопасности:")
        logger.info("   1. Создайте администратора через админ-панель")
        logger.info("   2. Настройте HTTPS для админ-панели")
        logger.info("   3. Регулярно обновляйте пароли")
        logger.info("   4. Мониторьте логи на предмет подозрительной активности")
    else:
        logger.error("❌ Миграция завершена с ошибками")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
