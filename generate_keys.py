#!/usr/bin/env python3
"""
Генератор безопасных ключей для Alex Orator Bot
Генерирует JWT_SECRET_KEY, SECRET_KEY и DB_PASSWORD для использования в .env файле
"""

import secrets
import string
import base64
import os
from datetime import datetime


def generate_jwt_secret_key(length=64):
    """Генерация JWT_SECRET_KEY"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_secret_key(length=32):
    """Генерация SECRET_KEY"""
    random_bytes = secrets.token_bytes(length)
    return base64.b64encode(random_bytes).decode("utf-8")


def generate_secure_password(length=20):
    """Генерация безопасного пароля для базы данных"""
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    symbols = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    # Минимум по одному символу каждого типа
    password = [secrets.choice(lowercase), secrets.choice(uppercase), secrets.choice(digits), secrets.choice(symbols)]

    # Добавляем остальные символы
    all_chars = lowercase + uppercase + digits + symbols
    password.extend(secrets.choice(all_chars) for _ in range(length - 4))

    # Перемешиваем
    password_list = list(password)
    secrets.SystemRandom().shuffle(password_list)
    return "".join(password_list)


def verify_key_strength(key, key_type):
    """Проверка силы ключа"""
    score = 0
    feedback = []

    # Длина
    if len(key) >= 32:
        score += 2
    elif len(key) >= 16:
        score += 1
    else:
        feedback.append("Ключ слишком короткий")

    # Разнообразие символов
    has_lower = any(c.islower() for c in key)
    has_upper = any(c.isupper() for c in key)
    has_digit = any(c.isdigit() for c in key)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in key)

    if has_lower:
        score += 1
    if has_upper:
        score += 1
    if has_digit:
        score += 1
    if has_special:
        score += 1

    # Энтропия
    unique_chars = len(set(key))
    if unique_chars >= len(key) * 0.7:
        score += 1

    # Оценка
    if score >= 5:
        strength = "🔒 Отличная"
    elif score >= 4:
        strength = "🟢 Хорошая"
    elif score >= 3:
        strength = "🟡 Средняя"
    else:
        strength = "🔴 Слабая"

    print(f"{key_type}: {strength} ({score}/6)")
    if feedback:
        print(f"   Рекомендации: {', '.join(feedback)}")


def generate_all_keys():
    """Генерация всех необходимых ключей"""
    print("🔐 Генерация безопасных ключей для Alex Orator Bot")
    print("=" * 60)

    # Генерируем ключи
    jwt_secret = generate_jwt_secret_key(64)
    secret_key = generate_secret_key(32)
    db_password = generate_secure_password(20)

    print(f"📅 Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    print("🔑 Сгенерированные ключи:")
    print("-" * 40)
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print(f"SECRET_KEY={secret_key}")
    print(f"DB_PASSWORD={db_password}")
    print()

    # Проверяем безопасность
    print("🔒 Проверка безопасности:")
    print("-" * 40)
    print(f"✅ JWT_SECRET_KEY: {len(jwt_secret)} символов")
    print(f"✅ SECRET_KEY: {len(secret_key)} символов (base64)")
    print(f"✅ DB_PASSWORD: {len(db_password)} символов")
    print()

    # Создаем .env файл
    env_content = f"""# Alex Orator Bot - Переменные окружения
# Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Telegram Bot
BOT_TOKEN=your_telegram_bot_token_here

# Backend API
BACKEND_URL=http://localhost:8000
API_TIMEOUT=30
API_RETRY_ATTEMPTS=3
API_RETRY_DELAY=1

# Базы данных (для Docker контейнеров)
APP_DATABASE_URL=postgresql://alex_orator:{db_password}@app-db:5432/app_db

# Пароль для баз данных
DB_PASSWORD={db_password}

# JWT и безопасность
JWT_SECRET_KEY={jwt_secret}
SECRET_KEY={secret_key}

# OpenAI (опционально, для будущих функций)
OPENAI_API_KEY=your_openai_api_key_here

# Логирование
LOG_LEVEL=INFO
DEBUG=false

# Настройки бота
DEFAULT_LANGUAGE=ru
MAX_PAIRS_PER_USER=3
DEFAULT_MATCHING_LIMIT=5
"""

    # Сохраняем в файл
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)

    print("💾 Файл .env создан с новыми ключами!")
    print()

    print("⚠️  ВАЖНО:")
    print("- Сохраните эти ключи в безопасном месте")
    print("- Никогда не коммитьте .env файл в git")
    print("- Используйте разные ключи для разных окружений")
    print("- Регулярно ротируйте ключи в продакшене")
    print()

    print("🚀 Следующие шаги:")
    print("1. Получите токен бота у @BotFather")
    print("2. Замените 'your_telegram_bot_token_here' на реальный токен")
    print("3. Запустите систему: ./start.sh start")
    print()

    return {"jwt_secret": jwt_secret, "secret_key": secret_key, "db_password": db_password}


def main():
    """Главная функция"""
    try:
        keys = generate_all_keys()

        print("🔍 Дополнительная проверка безопасности:")
        print("-" * 40)
        verify_key_strength(keys["jwt_secret"], "JWT_SECRET_KEY")
        verify_key_strength(keys["secret_key"], "SECRET_KEY")
        verify_key_strength(keys["db_password"], "DB_PASSWORD")
        print()

        print("✅ Генерация ключей завершена успешно!")

    except Exception as e:
        print(f"❌ Ошибка при генерации ключей: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
