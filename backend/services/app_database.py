import asyncpg
from typing import Optional, List
from loguru import logger
from datetime import datetime

from config.settings import settings
from models.orator import User
from models.user_settings import UserSettings


class AppDatabaseService:
    def __init__(self):
        self.database_url = settings.app_database_url
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Подключение к базе данных"""
        try:
            self.pool = await asyncpg.create_pool(self.database_url)
            await self._create_tables()
            logger.info("Connected to application database")
        except Exception as e:
            logger.error(f"Failed to connect to app database: {e}")
            raise

    async def disconnect(self):
        """Отключение от базы данных"""
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from application database")

    async def check_connection(self):
        """Проверка подключения к базе данных"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            raise

    async def _create_tables(self):
        """Создание таблиц приложения"""
        async with self.pool.acquire() as conn:
            # Таблица пользователей
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    email VARCHAR(255) UNIQUE NOT NULL,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    telegram_id VARCHAR(100) UNIQUE,
                    telegram_username VARCHAR(100),
                    is_active BOOLEAN DEFAULT TRUE,
                    is_superuser BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Таблица настроек пользователей
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_settings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    language VARCHAR(10) DEFAULT 'ru',
                    show_explanations BOOLEAN DEFAULT TRUE,
                    show_sql BOOLEAN DEFAULT TRUE,
                    max_results INTEGER DEFAULT 100,
                    auto_format BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Таблица истории запросов
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS query_history (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    natural_query TEXT,
                    sql_query TEXT,
                    explanation TEXT,
                    execution_time FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Таблица описаний базы данных
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS database_descriptions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    table_name VARCHAR(255) NOT NULL,
                    column_name VARCHAR(255),
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Таблица подписчиков каналов
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS channel_subscribers (
                    id SERIAL PRIMARY KEY,
                    chat_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    status VARCHAR(20) NOT NULL CHECK (status IN ('member', 'left', 'kicked', 'administrator', 'creator')),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(chat_id, user_id)
                )
            """
            )

            # Индексы для таблицы channel_subscribers
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_channel_subscribers_chat_id ON channel_subscribers(chat_id)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_channel_subscribers_user_id ON channel_subscribers(user_id)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_channel_subscribers_status ON channel_subscribers(status)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_channel_subscribers_updated_at ON channel_subscribers(updated_at)"
            )

            logger.info("Application database tables created/verified")

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Получение пользователя по ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
            if row:
                return User(**dict(row))
            return None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Получение пользователя по username"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
            if row:
                return User(**dict(row))
            return None

    async def get_user_by_telegram_id(self, telegram_id: str) -> Optional[User]:
        """Получение пользователя по Telegram ID"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", telegram_id)
            if row:
                return User(**dict(row))
            return None

    async def create_user(self, user_data: dict) -> User:
        """Создание нового пользователя"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO users (email, username, hashed_password, first_name, last_name)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING *
            """,
                user_data["email"],
                user_data["username"],
                user_data["hashed_password"],
                user_data.get("first_name"),
                user_data.get("last_name"),
            )
            return User(**dict(row))

    async def create_telegram_user(self, telegram_data: dict) -> User:
        """Создание пользователя через Telegram"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO users (telegram_id, username, first_name, last_name)
                VALUES ($1, $2, $3, $4)
                RETURNING *
            """,
                telegram_data["telegram_id"],
                telegram_data.get("telegram_username"),
                telegram_data.get("first_name"),
                telegram_data.get("last_name"),
            )
            return User(**dict(row))

    async def get_user_settings(self, user_id: str) -> Optional[UserSettings]:
        """Получение настроек пользователя"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM user_settings WHERE user_id = $1", user_id)
            if row:
                return UserSettings(**dict(row))
            return None

    async def create_user_settings(self, user_id: str, settings_data: dict) -> UserSettings:
        """Создание настроек пользователя"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO user_settings (user_id, language, show_explanations, show_sql, max_results, auto_format)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
            """,
                user_id,
                settings_data.get("language", "ru"),
                settings_data.get("show_explanations", True),
                settings_data.get("show_sql", True),
                settings_data.get("max_results", 100),
                settings_data.get("auto_format", True),
            )
            return UserSettings(**dict(row))

    async def update_user_settings(self, user_id: str, settings_data: dict) -> UserSettings:
        """Обновление настроек пользователя"""
        async with self.pool.acquire() as conn:
            # Сначала проверяем, существуют ли настройки
            existing = await self.get_user_settings(user_id)
            if not existing:
                return await self.create_user_settings(user_id, settings_data)

            # Обновляем существующие настройки
            set_clause = []
            values = [user_id]
            param_count = 1

            for key, value in settings_data.items():
                if value is not None:
                    set_clause.append(f"{key} = ${param_count + 1}")
                    values.append(value)
                    param_count += 1

            if not set_clause:
                return existing

            set_clause.append("updated_at = CURRENT_TIMESTAMP")
            query = f"""
                UPDATE user_settings 
                SET {', '.join(set_clause)}
                WHERE user_id = $1
                RETURNING *
            """

            row = await conn.fetchrow(query, *values)
            return UserSettings(**dict(row))

    async def save_query_history(
        self, user_id: str, natural_query: str, sql_query: str, explanation: str = None, execution_time: float = None
    ):
        """Сохранение истории запросов"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO query_history (user_id, natural_query, sql_query, explanation, execution_time)
                VALUES ($1, $2, $3, $4, $5)
            """,
                user_id,
                natural_query,
                sql_query,
                explanation,
                execution_time,
            )


# Создание экземпляра сервиса
app_database_service = AppDatabaseService()
