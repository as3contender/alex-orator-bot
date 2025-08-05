import asyncpg
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Загружаем переменные окружения из .env файла
load_dotenv("../.env")


def build_database_url():
    """Собирает URL для подключения к базе данных из отдельных параметров"""
    host = os.getenv("APP_DATABASE_HOST", "localhost")
    port = os.getenv("APP_DATABASE_PORT", "5434")
    user = os.getenv("APP_DATABASE_LOGIN", "alex_orator")
    password = os.getenv("APP_DATABASE_PASSWORD", "")
    database = os.getenv("APP_DATABASE_NAME", "app_db")

    # Экранируем специальные символы в пароле для URL
    escaped_password = quote_plus(password)

    return f"postgresql://{user}:{escaped_password}@{host}:{port}/{database}"


async def get_db_pool():
    database_url = build_database_url()
    return await asyncpg.create_pool(database_url)
