# -----------------------------------------------------------------------------
# db.py — минимальные правки для совместимости (если нужно)
# -----------------------------------------------------------------------------
# Оставь свою реализацию, важно лишь, чтобы были функции:
#   - async def get_db_pool() -> asyncpg.Pool
#   - async def close_db_pool() -> None
# и чтобы пул создавался ОДИН раз и закрывался ОДИН раз.


# Примерный каркас (адаптируй к своему build_database_url):

import asyncpg
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

_db_pool: asyncpg.Pool | None = None


def build_database_url() -> str:
    """Собирает URL для подключения к базе данных из отдельных параметров"""

    host = os.getenv("APP_DATABASE_HOST", "localhost")
    port = os.getenv("APP_DATABASE_PORT", "5434")
    user = os.getenv("APP_DATABASE_LOGIN", "alex_orator")
    password = os.getenv("APP_DATABASE_PASSWORD", "")
    database = os.getenv("APP_DATABASE_NAME", "app_db")

    # Экранируем специальные символы в пароле для URL
    escaped_password = quote_plus(password)

    return f"postgresql://{user}:{escaped_password}@{host}:{port}/{database}"


async def get_db_pool() -> asyncpg.Pool:
    global _db_pool
    if _db_pool is None:
        _db_pool = await asyncpg.create_pool(dsn=build_database_url(), min_size=1, max_size=10)
    return _db_pool


async def close_db_pool() -> None:
    global _db_pool
    if _db_pool is not None:
        await _db_pool.close()
        _db_pool = None
