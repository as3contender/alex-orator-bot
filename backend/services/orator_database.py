import asyncpg
from typing import Optional, List, Dict, Any
from models.orator.message_queue import MessageQueue
from loguru import logger
from datetime import datetime, date, timedelta
from uuid import UUID

from config.settings import settings
from models.orator import (
    UserProfile,
    WeekRegistration,
    UserTopic,
    UserPair,
    SessionFeedback,
    BotContent,
    RegistrationStatus,
    PairStatus,
    FeedbackRating,
    Gender,
)


class OratorDatabaseService:
    def __init__(self):
        self.database_url = settings.app_database_url
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Подключение к базе данных"""
        try:
            self.pool = await asyncpg.create_pool(self.database_url)
            # Временно отключаем создание таблиц для отладки
            # await self._create_orator_tables()
            logger.info("Connected to orator database")
        except Exception as e:
            logger.error(f"Failed to connect to orator database: {e}")
            raise

    async def disconnect(self):
        """Отключение от базы данных"""
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from orator database")

    async def _create_orator_tables(self):
        """Создание таблиц для ораторского бота"""
        async with self.pool.acquire() as conn:
            # Расширение таблицы пользователей для ораторского бота
            await conn.execute(
                """
                ALTER TABLE users ADD COLUMN IF NOT EXISTS 
                gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other'))
                """
            )
            await conn.execute(
                """
                ALTER TABLE users ADD COLUMN IF NOT EXISTS 
                total_sessions INTEGER DEFAULT 0
                """
            )
            await conn.execute(
                """
                ALTER TABLE users ADD COLUMN IF NOT EXISTS 
                feedback_count INTEGER DEFAULT 0
                """
            )

            # Таблица настроек ораторского бота
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS orator_settings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    key VARCHAR(100) UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Таблица регистраций на недели
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS week_registrations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    week_start_date DATE NOT NULL,
                    week_end_date DATE NOT NULL,
                    preferred_time_msk VARCHAR(5) NOT NULL,
                    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'cancelled')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cancelled_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Таблица выбранных тем пользователей
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_topics (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    week_registration_id UUID REFERENCES week_registrations(id) ON DELETE CASCADE,
                    topic_path VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Таблица пар пользователей
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_pairs (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user1_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    user2_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    week_registration_id UUID REFERENCES week_registrations(id) ON DELETE CASCADE,
                    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'cancelled')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confirmed_at TIMESTAMP,
                    cancelled_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Таблица обратной связи
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_feedback (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    pair_id UUID REFERENCES user_pairs(id) ON DELETE CASCADE,
                    from_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
                    feedback_text TEXT NOT NULL,
                    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Таблица контента бота
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS bot_content (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    content_key VARCHAR(100) NOT NULL,
                    content_text TEXT NOT NULL,
                    language VARCHAR(10) DEFAULT 'ru',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Добавляем уникальное ограничение, если его нет
            try:
                await conn.execute(
                    """
                    ALTER TABLE bot_content 
                    ADD CONSTRAINT bot_content_key_language_unique 
                    UNIQUE(content_key, language)
                    """
                )
            except Exception:
                # Ограничение уже существует
                pass

            # Таблица тем
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS topics (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    topic_id VARCHAR(100) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    parent_id UUID REFERENCES topics(id) ON DELETE CASCADE,
                    level INTEGER DEFAULT 1,
                    sort_order INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Создание индексов для оптимизации
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_week_registrations_user_id ON week_registrations(user_id)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_week_registrations_week_dates ON week_registrations(week_start_date, week_end_date)"
            )
            await conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_topics_registration_id ON user_topics(week_registration_id)"
            )
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_pairs_users ON user_pairs(user1_id, user2_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_user_pairs_status ON user_pairs(status)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_session_feedback_pair_id ON session_feedback(pair_id)")

            # Таблица очереди сообщений
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS message_queue (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id VARCHAR(100) NOT NULL,
                    message TEXT NOT NULL,
                    keyboard JSONB,
                    sent BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_at TIMESTAMP
                )
            """
            )

            # Инициализация базового контента
            # await self._initialize_bot_content(conn)

            # Инициализация настроек по умолчанию
            await self._initialize_default_settings(conn)

            # Инициализация тем
            # await self._initialize_topics(conn)

    async def _initialize_bot_content(self, conn):
        """Инициализация базового контента бота"""
        content_data = [
            {
                "key": "welcome_message",
                "text": """🎭 **Добро пожаловать в Alex Orator Bot!**

Я помогу вам найти партнера для тренировки ораторского искусства.

**Что я умею:**
• Подбирать пары для занятий
• Организовывать недельные сессии
• Отслеживать ваш прогресс
• Собирать обратную связь

**Основные команды:**
/register - Зарегистрироваться на неделю
/match - Подобрать пару
/pairs - Мои пары
/feedback - Оставить обратную связь
/profile - Мой профиль
/help - Справка

Начните с регистрации на неделю! 🚀""",
                "language": "ru",
            },
            {
                "key": "help_message",
                "text": """📚 **Справка по командам**

**Основные команды:**
/start - Начало работы
/register - Регистрация на неделю занятий
/cancel - Отмена регистрации
/match - Подобрать пару для занятий
/pairs - Просмотр своих пар
/feedback - Оставить обратную связь
/profile - Мой профиль и статистика
/help - Эта справка

**Как это работает:**
1. Регистрируетесь на неделю
2. Выбираете удобное время и темы
3. Получаете 3 кандидата для выбора
4. Подтверждаете пару
5. Проводите занятие
6. Оставляете обратную связь

**Важно:** Для повторной регистрации необходимо оставить обратную связь по всем занятиям!""",
                "language": "ru",
            },
        ]

        for content in content_data:
            await conn.execute(
                """
                INSERT INTO bot_content (content_key, content_text, language, is_active)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (content_key, language) DO NOTHING
                """,
                content["key"],
                content["text"],
                content["language"],
                True,
            )

    async def _initialize_default_settings(self, conn):
        """Инициализация настроек по умолчанию"""
        default_settings = [
            {"key": "max_pairs_per_user", "value": "3", "description": "Максимальное количество пар на пользователя"},
            {
                "key": "max_candidates_per_request",
                "value": "3",
                "description": "Максимальное количество кандидатов в одном запросе",
            },
            {
                "key": "registration_deadline_hours",
                "value": "24",
                "description": "Время до дедлайна регистрации в часах",
            },
            {
                "key": "feedback_required_for_reregistration",
                "value": "true",
                "description": "Требуется ли обратная связь для повторной регистрации",
            },
            {"key": "min_feedback_length", "value": "3", "description": "Минимальная длина обратной связи"},
            {"key": "max_feedback_length", "value": "1000", "description": "Максимальная длина обратной связи"},
            {"key": "session_duration_minutes", "value": "60", "description": "Продолжительность сессии в минутах"},
            {
                "key": "auto_cancel_pending_pairs_hours",
                "value": "48",
                "description": "Автоматическая отмена ожидающих пар через часы",
            },
        ]

        for setting in default_settings:
            await conn.execute(
                """
                INSERT INTO orator_settings (key, value, description, is_active)
                VALUES ($1, $2, $3, TRUE)
                ON CONFLICT (key) DO NOTHING
                """,
                setting["key"],
                setting["value"],
                setting["description"],
            )

    async def _initialize_topics(self, conn):
        """Инициализация тем по умолчанию"""
        topics_data = [
            # Группа 1
            {"topic_id": "group1", "name": "Группа 1", "level": 1, "sort_order": 1},
            {
                "topic_id": "group1_level1",
                "name": "Группа 1 - Уровень 1",
                "parent_id": "group1",
                "level": 2,
                "sort_order": 1,
            },
            {
                "topic_id": "group1_level2",
                "name": "Группа 1 - Уровень 2",
                "parent_id": "group1",
                "level": 2,
                "sort_order": 2,
            },
            {
                "topic_id": "group1_level3",
                "name": "Группа 1 - Уровень 3",
                "parent_id": "group1",
                "level": 2,
                "sort_order": 3,
            },
            # Группа 2
            {"topic_id": "group2", "name": "Группа 2", "level": 1, "sort_order": 2},
            {
                "topic_id": "group2_level1",
                "name": "Группа 2 - Уровень 1",
                "parent_id": "group2",
                "level": 2,
                "sort_order": 1,
            },
            {
                "topic_id": "group2_level2",
                "name": "Группа 2 - Уровень 2",
                "parent_id": "group2",
                "level": 2,
                "sort_order": 2,
            },
            {
                "topic_id": "group2_level3",
                "name": "Группа 2 - Уровень 3",
                "parent_id": "group2",
                "level": 2,
                "sort_order": 3,
            },
            # Группа 3
            {"topic_id": "group3", "name": "Группа 3", "level": 1, "sort_order": 3},
            {
                "topic_id": "group3_level1",
                "name": "Группа 3 - Уровень 1",
                "parent_id": "group3",
                "level": 2,
                "sort_order": 1,
            },
            {
                "topic_id": "group3_level2",
                "name": "Группа 3 - Уровень 2",
                "parent_id": "group3",
                "level": 2,
                "sort_order": 2,
            },
            {
                "topic_id": "group3_level3",
                "name": "Группа 3 - Уровень 3",
                "parent_id": "group3",
                "level": 2,
                "sort_order": 3,
            },
        ]

        for topic in topics_data:
            # Сначала вставляем родительские темы
            if "parent_id" not in topic:
                await conn.execute(
                    """
                    INSERT INTO topics (topic_id, name, level, sort_order, is_active)
                    VALUES ($1, $2, $3, $4, TRUE)
                    ON CONFLICT (topic_id) DO NOTHING
                    """,
                    topic["topic_id"],
                    topic["name"],
                    topic["level"],
                    topic["sort_order"],
                )
            else:
                # Для дочерних тем сначала получаем ID родителя
                parent_id = await conn.fetchval("SELECT id FROM topics WHERE topic_id = $1", topic["parent_id"])

                if parent_id:
                    await conn.execute(
                        """
                        INSERT INTO topics (topic_id, name, parent_id, level, sort_order, is_active)
                        VALUES ($1, $2, $3, $4, $5, TRUE)
                        ON CONFLICT (topic_id) DO NOTHING
                        """,
                        topic["topic_id"],
                        topic["name"],
                        parent_id,
                        topic["level"],
                        topic["sort_order"],
                    )

    # Методы для работы с пользователями
    async def get_user_profile(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Получить профиль пользователя"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    u.telegram_id, u.username, u.first_name, u.last_name,
                    u.gender, u.created_at as registration_date,
                    u.total_sessions, u.feedback_count, u.is_active
                FROM users u
                WHERE u.id = $1
                """,
                user_id,
            )
            return dict(row) if row else None

    async def update_user_profile(self, user_id: UUID, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Обновить профиль пользователя"""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE users 
                SET 
                    gender = COALESCE($2, gender),
                    first_name = COALESCE($3, first_name),
                    last_name = COALESCE($4, last_name),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = $1
                """,
                user_id,
                profile_data.get("gender"),
                profile_data.get("first_name"),
                profile_data.get("last_name"),
            )

            if result == "UPDATE 0":
                return None

            # Возвращаем обновленный профиль
            return await self.get_user_profile(user_id)

    async def get_user_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Получить статистику пользователя"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    u.total_sessions,
                    u.feedback_count,
                    COUNT(DISTINCT wr.id) as total_registrations,
                    COUNT(DISTINCT up.id) as total_pairs,
                    COUNT(DISTINCT CASE WHEN up.status = 'confirmed' THEN up.id END) as confirmed_pairs
                FROM users u
                LEFT JOIN week_registrations wr ON u.id = wr.user_id
                LEFT JOIN user_pairs up ON (u.id = up.user1_id OR u.id = up.user2_id)
                WHERE u.id = $1
                GROUP BY u.id, u.total_sessions, u.feedback_count
                """,
                user_id,
            )
            return (
                dict(row)
                if row
                else {
                    "total_sessions": 0,
                    "feedback_count": 0,
                    "total_registrations": 0,
                    "total_pairs": 0,
                    "confirmed_pairs": 0,
                }
            )

    # Методы для работы с недельными регистрациями
    async def create_week_registration(
        self, user_id: UUID, week_start: date, week_end: date, preferred_time: str, selected_topics: List[str] = None
    ) -> UUID:
        """Создать регистрацию на неделю"""
        async with self.pool.acquire() as conn:
            # Создаем регистрацию
            registration_id = await conn.fetchval(
                """
                INSERT INTO week_registrations 
                (user_id, week_start_date, week_end_date, preferred_time_msk)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                user_id,
                week_start,
                week_end,
                preferred_time,
            )

            # Добавляем выбранные темы, если они есть
            if selected_topics:
                await self.add_user_topics(user_id, registration_id, selected_topics)

            # Возвращаем созданную регистрацию
            row = await conn.fetchrow(
                """
                SELECT * FROM week_registrations WHERE id = $1
                """,
                registration_id,
            )
            registration = dict(row) if row else None

            if registration and selected_topics:
                registration["selected_topics"] = selected_topics

            return registration

    async def get_user_week_registration(self, user_id: UUID, week_start: date = None) -> Optional[Dict[str, Any]]:
        """Получить регистрацию пользователя на неделю"""
        async with self.pool.acquire() as conn:
            if week_start is None:
                # Получаем текущую активную регистрацию
                row = await conn.fetchrow(
                    """
                    SELECT * FROM week_registrations
                    WHERE user_id = $1 AND status = 'active' AND week_end_date >= CURRENT_DATE
                    ORDER BY week_start_date DESC
                    LIMIT 1
                    """,
                    user_id,
                )
            else:
                # Получаем регистрацию на конкретную неделю
                row = await conn.fetchrow(
                    """
                    SELECT * FROM week_registrations
                    WHERE user_id = $1 AND week_start_date = $2
                    """,
                    user_id,
                    week_start,
                )

            if not row:
                return None

            registration = dict(row)

            # Получаем выбранные темы
            topics = await self.get_user_topics(registration["id"])
            registration["selected_topics"] = topics

            return registration

    async def cancel_week_registration(self, user_id: UUID, week_start: date) -> bool:
        """Отменить регистрацию на неделю"""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE week_registrations 
                SET status = 'cancelled', cancelled_at = CURRENT_TIMESTAMP
                WHERE user_id = $1 AND week_start_date = $2 AND status = 'active'
                """,
                user_id,
                week_start,
            )
            return result != "UPDATE 0"

    # Методы для работы с темами
    async def add_user_topics(self, user_id: UUID, registration_id: UUID, topics: List[str]) -> bool:
        """Добавить выбранные темы пользователя"""
        async with self.pool.acquire() as conn:
            for topic in topics:
                await conn.execute(
                    """
                    INSERT INTO user_topics (user_id, week_registration_id, topic_path)
                    VALUES ($1, $2, $3)
                    """,
                    user_id,
                    registration_id,
                    topic,
                )
            return True

    async def update_user_topics(self, registration_id: UUID, topics: List[str]) -> bool:
        """Обновить выбранные темы пользователя"""
        async with self.pool.acquire() as conn:
            # Удаляем старые темы
            await conn.execute(
                """
                DELETE FROM user_topics
                WHERE week_registration_id = $1
                """,
                registration_id,
            )

            # Добавляем новые темы
            for topic in topics:
                await conn.execute(
                    """
                    INSERT INTO user_topics (user_id, week_registration_id, topic_path)
                    SELECT user_id, $1, $2
                    FROM week_registrations
                    WHERE id = $1
                    """,
                    registration_id,
                    topic,
                )
            return True

    async def get_user_topics(self, registration_id: UUID) -> List[str]:
        """Получить темы пользователя для регистрации"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT topic_path FROM user_topics
                WHERE week_registration_id = $1
                """,
                registration_id,
            )
            return [row["topic_path"] for row in rows]

    # Методы для работы с парами
    async def create_user_pair(self, user1_id: UUID, user2_id: UUID, registration_id: UUID) -> Optional[Dict[str, Any]]:
        """Создать пару пользователей"""
        async with self.pool.acquire() as conn:
            pair_id = await conn.fetchval(
                """
                INSERT INTO user_pairs (user1_id, user2_id, week_registration_id)
                VALUES ($1, $2, $3)
                RETURNING id
                """,
                user1_id,
                user2_id,
                registration_id,
            )

            # Возвращаем полную информацию о созданной паре
            row = await conn.fetchrow(
                """
                SELECT 
                    up.id, up.status, up.created_at, up.confirmed_at, up.cancelled_at,
                    up.user1_id, up.user2_id,
                    up.user2_id as partner_id,
                    COALESCE(u2.username, '') as partner_username,
                    u2.telegram_id as partner_telegram_id,
                    u2.first_name || ' ' || COALESCE(u2.last_name, '') as partner_name,
                    wr.week_start_date, wr.week_end_date,
                    TRUE as is_initiator
                FROM user_pairs up
                JOIN week_registrations wr ON up.week_registration_id = wr.id
                JOIN users u1 ON up.user1_id = u1.id
                JOIN users u2 ON up.user2_id = u2.id
                WHERE up.id = $1
                """,
                pair_id,
            )
            return dict(row) if row else None

    async def confirm_user_pair(self, pair_id: UUID, confirmed: bool, user_id: UUID = None) -> Optional[Dict[str, Any]]:
        """Подтвердить или отклонить пару"""
        async with self.pool.acquire() as conn:
            # Сначала проверяем, существует ли пара
            pair_exists = await conn.fetchval(
                """
                SELECT id FROM user_pairs WHERE id = $1
                """,
                pair_id,
            )

            if not pair_exists:
                return None

            # Проверяем текущий статус пары
            current_status = await conn.fetchval(
                """
                SELECT status FROM user_pairs WHERE id = $1
                """,
                pair_id,
            )

            # Если пара уже подтверждена и мы пытаемся подтвердить её снова
            if confirmed and current_status == "confirmed":
                # Возвращаем информацию о паре без обновления
                row = await conn.fetchrow(
                    """
                    SELECT 
                        up.id, up.status, up.created_at, up.confirmed_at, up.cancelled_at,
                        up.user1_id, up.user2_id,
                        CASE 
                            WHEN up.user1_id = $2 THEN up.user2_id
                            ELSE up.user1_id
                        END as partner_id,
                        CASE 
                            WHEN up.user1_id = $2 THEN COALESCE(u2.username, '')
                            ELSE COALESCE(u1.username, '')
                        END as partner_username,
                        CASE 
                            WHEN up.user1_id = $2 THEN u2.telegram_id
                            ELSE u1.telegram_id
                        END as partner_telegram_id,
                        CASE 
                            WHEN up.user1_id = $2 THEN u2.first_name || ' ' || COALESCE(u2.last_name, '')
                            ELSE u1.first_name || ' ' || COALESCE(u1.last_name, '')
                        END as partner_name,
                        wr.week_start_date, wr.week_end_date,
                        CASE 
                            WHEN up.user1_id = $2 THEN TRUE
                            ELSE FALSE
                        END as is_initiator
                    FROM user_pairs up
                    JOIN week_registrations wr ON up.week_registration_id = wr.id
                    JOIN users u1 ON up.user1_id = u1.id
                    JOIN users u2 ON up.user2_id = u2.id
                    WHERE up.id = $1
                    """,
                    pair_id,
                    user_id,
                )
                return dict(row) if row else None

            # Если пара уже отменена и мы пытаемся отменить её снова
            if not confirmed and current_status == "cancelled":
                # Возвращаем информацию о паре без обновления
                row = await conn.fetchrow(
                    """
                    SELECT 
                        up.id, up.status, up.created_at, up.confirmed_at, up.cancelled_at,
                        up.user1_id, up.user2_id,
                        CASE 
                            WHEN up.user1_id = $2 THEN up.user2_id
                            ELSE up.user1_id
                        END as partner_id,
                        CASE 
                            WHEN up.user1_id = $2 THEN COALESCE(u2.username, '')
                            ELSE COALESCE(u1.username, '')
                        END as partner_username,
                        CASE 
                            WHEN up.user1_id = $2 THEN u2.telegram_id
                            ELSE u1.telegram_id
                        END as partner_telegram_id,
                        CASE 
                            WHEN up.user1_id = $2 THEN u2.first_name || ' ' || COALESCE(u2.last_name, '')
                            ELSE u1.first_name || ' ' || COALESCE(u1.last_name, '')
                        END as partner_name,
                        wr.week_start_date, wr.week_end_date,
                        CASE 
                            WHEN up.user1_id = $2 THEN TRUE
                            ELSE FALSE
                        END as is_initiator
                    FROM user_pairs up
                    JOIN week_registrations wr ON up.week_registration_id = wr.id
                    JOIN users u1 ON up.user1_id = u1.id
                    JOIN users u2 ON up.user2_id = u2.id
                    WHERE up.id = $1
                    """,
                    pair_id,
                    user_id,
                )
                return dict(row) if row else None

            # Обновляем статус только если пара в статусе pending
            if confirmed:
                result = await conn.execute(
                    """
                    UPDATE user_pairs 
                    SET status = 'confirmed', confirmed_at = CURRENT_TIMESTAMP
                    WHERE id = $1 AND status = 'pending'
                    """,
                    pair_id,
                )
            else:
                result = await conn.execute(
                    """
                    UPDATE user_pairs 
                    SET status = 'cancelled', cancelled_at = CURRENT_TIMESTAMP
                    WHERE id = $1 AND status = 'pending'
                    """,
                    pair_id,
                )

            if result == "UPDATE 0":
                return None

            # Возвращаем обновленную пару
            row = await conn.fetchrow(
                """
                SELECT 
                    up.id, up.status, up.created_at, up.confirmed_at, up.cancelled_at,
                    up.user1_id, up.user2_id,
                    CASE 
                        WHEN up.user1_id = $2 THEN up.user2_id
                        ELSE up.user1_id
                    END as partner_id,
                    CASE 
                        WHEN up.user1_id = $2 THEN COALESCE(u2.username, '')
                        ELSE COALESCE(u1.username, '')
                    END as partner_username,
                    CASE 
                        WHEN up.user1_id = $2 THEN u2.telegram_id
                        ELSE u1.telegram_id
                    END as partner_telegram_id,
                    CASE 
                        WHEN up.user1_id = $2 THEN u2.first_name || ' ' || COALESCE(u2.last_name, '')
                        ELSE u1.first_name || ' ' || COALESCE(u1.last_name, '')
                    END as partner_name,
                    wr.week_start_date, wr.week_end_date,
                    CASE 
                        WHEN up.user1_id = $2 THEN TRUE
                        ELSE FALSE
                    END as is_initiator
                FROM user_pairs up
                JOIN week_registrations wr ON up.week_registration_id = wr.id
                JOIN users u1 ON up.user1_id = u1.id
                JOIN users u2 ON up.user2_id = u2.id
                WHERE up.id = $1
                """,
                pair_id,
                user_id,
            )
            return dict(row) if row else None

    async def cancel_user_pair(self, pair_id: UUID, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Отменить пару"""
        async with self.pool.acquire() as conn:
            # Сначала проверяем, существует ли пара
            pair_exists = await conn.fetchval(
                """
                SELECT id FROM user_pairs WHERE id = $1
                """,
                pair_id,
            )

            if not pair_exists:
                return None

            # Проверяем текущий статус пары
            current_status = await conn.fetchval(
                """
                SELECT status FROM user_pairs WHERE id = $1
                """,
                pair_id,
            )

            # Если пара уже отменена, возвращаем её информацию
            if current_status == "cancelled":
                # Возвращаем информацию о паре без обновления
                row = await conn.fetchrow(
                    """
                    SELECT 
                        up.id, up.status, up.created_at, up.confirmed_at, up.cancelled_at,
                        up.user1_id, up.user2_id,
                        CASE 
                            WHEN up.user1_id = $2 THEN up.user2_id
                            ELSE up.user1_id
                        END as partner_id,
                        CASE 
                            WHEN up.user1_id = $2 THEN u2.username
                            ELSE u1.username
                        END as partner_username,
                        CASE 
                            WHEN up.user1_id = $2 THEN u2.first_name || ' ' || COALESCE(u2.last_name, '')
                            ELSE u1.first_name || ' ' || COALESCE(u1.last_name, '')
                        END as partner_name,
                        wr.week_start_date, wr.week_end_date,
                        CASE 
                            WHEN up.user1_id = $2 THEN TRUE
                            ELSE FALSE
                        END as is_initiator
                    FROM user_pairs up
                    JOIN week_registrations wr ON up.week_registration_id = wr.id
                    JOIN users u1 ON up.user1_id = u1.id
                    JOIN users u2 ON up.user2_id = u2.id
                    WHERE up.id = $1
                    """,
                    pair_id,
                    user_id,
                )
                return dict(row) if row else None

            # Обновляем статус только если пара не отменена
            result = await conn.execute(
                """
                UPDATE user_pairs 
                SET status = 'cancelled', cancelled_at = CURRENT_TIMESTAMP
                WHERE id = $1 AND status IN ('pending', 'confirmed')
                """,
                pair_id,
            )

            if result == "UPDATE 0":
                return None

            # Возвращаем обновленную пару с полной информацией
            row = await conn.fetchrow(
                """
                SELECT 
                    up.id, up.status, up.created_at, up.confirmed_at, up.cancelled_at,
                    up.user1_id, up.user2_id,
                    CASE 
                        WHEN up.user1_id = $2 THEN up.user2_id
                        ELSE up.user1_id
                    END as partner_id,
                    CASE 
                        WHEN up.user1_id = $2 THEN u2.username
                        ELSE u1.username
                    END as partner_username,
                    CASE 
                        WHEN up.user1_id = $2 THEN u2.first_name || ' ' || COALESCE(u2.last_name, '')
                        ELSE u1.first_name || ' ' || COALESCE(u1.last_name, '')
                    END as partner_name,
                    wr.week_start_date, wr.week_end_date,
                    CASE 
                        WHEN up.user1_id = $2 THEN TRUE
                        ELSE FALSE
                    END as is_initiator
                FROM user_pairs up
                JOIN week_registrations wr ON up.week_registration_id = wr.id
                JOIN users u1 ON up.user1_id = u1.id
                JOIN users u2 ON up.user2_id = u2.id
                WHERE up.id = $1
                """,
                pair_id,
                user_id,
            )
            return dict(row) if row else None

    async def get_user_pairs(self, user_id: UUID, week_start: date) -> List[Dict[str, Any]]:
        """Получить пары пользователя на неделю"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    up.id, up.status, up.created_at, up.confirmed_at, up.cancelled_at,
                    CASE 
                        WHEN up.user1_id = $1 THEN up.user2_id
                        ELSE up.user1_id
                    END as partner_id,
                    CASE 
                        WHEN up.user1_id = $1 THEN COALESCE(u2.username, '')
                        ELSE COALESCE(u1.username, '')
                    END as partner_username,
                    CASE 
                        WHEN up.user1_id = $1 THEN COALESCE(u2.telegram_id, '')
                        ELSE COALESCE(u1.telegram_id, '')
                    END as partner_telegram_id,
                    CASE 
                        WHEN up.user1_id = $1 THEN u2.first_name || ' ' || COALESCE(u2.last_name, '')
                        ELSE u1.first_name || ' ' || COALESCE(u1.last_name, '')
                    END as partner_name,
                    wr.week_start_date, wr.week_end_date,
                    CASE 
                        WHEN up.user1_id = $1 THEN TRUE
                        ELSE FALSE
                    END as is_initiator
                FROM user_pairs up
                JOIN week_registrations wr ON up.week_registration_id = wr.id
                JOIN users u1 ON up.user1_id = u1.id
                JOIN users u2 ON up.user2_id = u2.id
                WHERE (up.user1_id = $1 OR up.user2_id = $1) 
                AND wr.week_start_date = $2
                AND up.status != 'cancelled'
                ORDER BY up.created_at DESC
                """,
                user_id,
                week_start,
            )
            return [dict(row) for row in rows]

    # Методы для работы с обратной связью
    async def create_session_feedback(
        self, pair_id: UUID, from_user_id: UUID, feedback_text: str, rating: int
    ) -> Optional[Dict[str, Any]]:
        """Создать обратную связь по занятию"""
        async with self.pool.acquire() as conn:
            feedback_id = await conn.fetchval(
                """
                INSERT INTO session_feedback 
                (pair_id, from_user_id, feedback_text, rating)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                pair_id,
                from_user_id,
                feedback_text,
                rating,
            )

            # Обновляем счетчики
            await conn.execute("UPDATE users SET feedback_count = feedback_count + 1 WHERE id = $1", from_user_id)

            # Возвращаем созданную обратную связь
            row = await conn.fetchrow(
                """
                SELECT * FROM session_feedback WHERE id = $1
                """,
                feedback_id,
            )
            return dict(row) if row else None

    async def get_session_feedback(self, pair_id: UUID) -> List[Dict[str, Any]]:
        """Получить обратную связь по паре"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    sf.id, sf.feedback_text, sf.rating, sf.created_at,
                    u.first_name || ' ' || COALESCE(u.last_name, '') as from_user_name
                FROM session_feedback sf
                JOIN users u ON sf.from_user_id = u.id
                WHERE sf.pair_id = $1
                ORDER BY sf.created_at DESC
                """,
                pair_id,
            )
            return [dict(row) for row in rows]

    async def get_session_feedback_by_user(
        self, from_user_id: UUID = None, to_user_id: UUID = None
    ) -> List[Dict[str, Any]]:
        """Получить обратную связь по пользователю"""
        async with self.pool.acquire() as conn:
            if from_user_id:
                # Получить данную обратную связь (которую пользователь оставил)
                rows = await conn.fetch(
                    """
                    SELECT 
                        sf.id, sf.pair_id, sf.feedback_text, sf.rating, sf.created_at,
                        up.partner_name
                    FROM session_feedback sf
                    JOIN user_pairs up ON sf.pair_id = up.id
                    WHERE sf.from_user_id = $1
                    ORDER BY sf.created_at DESC
                    """,
                    from_user_id,
                )
            elif to_user_id:
                # Получить полученную обратную связь (оставленную другими пользователями для пар, где участвует данный пользователь)
                rows = await conn.fetch(
                    """
                    SELECT 
                        sf.id, sf.pair_id, sf.feedback_text, sf.rating, sf.created_at,
                        u.first_name || ' ' || COALESCE(u.last_name, '') as from_user_name
                    FROM session_feedback sf
                    JOIN user_pairs up ON sf.pair_id = up.id
                    JOIN users u ON sf.from_user_id = u.id
                    WHERE (up.user1_id = $1 OR up.user2_id = $1) AND sf.from_user_id != $1
                    ORDER BY sf.created_at DESC
                    """,
                    to_user_id,
                )
            else:
                return []

            return [dict(row) for row in rows]

    # Методы для работы с контентом
    async def get_topic_tree(self) -> Dict[str, Any]:
        """Получить дерево тем из базы данных"""
        async with self.pool.acquire() as conn:
            # Получаем все темы, отсортированные по уровню и порядку
            rows = await conn.fetch(
                """
                SELECT id, topic_id, name, description, parent_id, level, sort_order
                FROM topics 
                WHERE is_active = TRUE
                ORDER BY level, sort_order
                """
            )

            # Создаем словарь для быстрого поиска тем по ID
            topics_dict = {}
            root_topics = []

            # Сначала создаем все темы
            for row in rows:
                topic = {"id": row["topic_id"], "name": row["name"], "description": row["description"], "children": []}
                topics_dict[row["id"]] = topic

                # Если это корневая тема (без родителя), добавляем в корневой список
                if row["parent_id"] is None:
                    root_topics.append(topic)

            # Теперь добавляем дочерние темы к родителям
            for row in rows:
                if row["parent_id"] is not None and row["parent_id"] in topics_dict:
                    parent_topic = topics_dict[row["parent_id"]]
                    child_topic = topics_dict[row["id"]]
                    parent_topic["children"].append(child_topic)

            return {"topics": root_topics, "language": "ru"}

    async def get_bot_content(self, content_key: str, language: str = "ru") -> Optional[str]:
        """Получить контент бота"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT content_text FROM bot_content
                WHERE content_key = $1 AND language = $2 AND is_active = TRUE
                """,
                content_key,
                language,
            )
            return row["content_text"] if row else None

    async def get_exercises_by_topic(self, topic_id: str, language: str = "ru") -> List[Dict[str, Any]]:
        """Получить все упражнения для указанной темы (дочерние элементы)"""
        async with self.pool.acquire() as conn:
            # Ищем все упражнения, которые начинаются с указанного topic_id
            logger.info(f"get_exercises_by_topic: {topic_id}, {language}")

            sql_query = """
                SELECT content_key, content_text, created_at, updated_at
                FROM bot_content bc
                inner join (select topic_id 
                    from topics t
                    inner join (
                        select id from topics t where t.topic_id = $1) q on t.parent_id = q.id) 
                        q on bc.content_key = 'exercise_'||q.topic_id
                    WHERE language = $2 AND is_active = TRUE
                ORDER BY content_key
                """

            rows = await conn.fetch(sql_query, topic_id, language)

            exercises = []
            for row in rows:
                # Извлекаем номер упражнения из content_key
                exercise_key = row["content_key"]
                exercise_number = exercise_key.replace(f"exercise_{topic_id}_", "")

                exercises.append(
                    {
                        "exercise_key": exercise_key,
                        "exercise_number": exercise_number,
                        "content_text": row["content_text"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    }
                )

            return exercises

    async def update_bot_content(self, content_key: str, content_text: str, language: str = "ru") -> bool:
        """Обновить контент бота"""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                INSERT INTO bot_content (content_key, content_text, language, is_active)
                VALUES ($1, $2, $3, TRUE)
                ON CONFLICT (content_key, language) 
                DO UPDATE SET 
                    content_text = EXCLUDED.content_text,
                    updated_at = CURRENT_TIMESTAMP
                """,
                content_key,
                content_text,
                language,
            )
            return result != "INSERT 0"

    async def get_all_bot_content(self, language: str = None, is_active: bool = None) -> List[Dict[str, Any]]:
        """Получить весь контент бота с фильтрацией"""
        async with self.pool.acquire() as conn:
            query = "SELECT id, content_key, content_text, language, is_active, created_at, updated_at FROM bot_content WHERE 1=1"
            params = []
            param_count = 0

            if language:
                param_count += 1
                query += f" AND language = ${param_count}"
                params.append(language)

            if is_active is not None:
                param_count += 1
                query += f" AND is_active = ${param_count}"
                params.append(is_active)

            query += " ORDER BY content_key, language"

            rows = await conn.fetch(query, *params)

            content_list = []
            for row in rows:
                content_list.append(
                    {
                        "id": row["id"],
                        "content_key": row["content_key"],
                        "content_text": row["content_text"],
                        "language": row["language"],
                        "is_active": row["is_active"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    }
                )

            return content_list

    async def get_bot_content_by_key(self, content_key: str, language: str = "ru") -> Optional[Dict[str, Any]]:
        """Получить контент бота по ключу с полной информацией"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, content_key, content_text, language, is_active, created_at, updated_at
                FROM bot_content
                WHERE content_key = $1 AND language = $2
                """,
                content_key,
                language,
            )

            if not row:
                return None

            return {
                "id": row["id"],
                "content_key": row["content_key"],
                "content_text": row["content_text"],
                "language": row["language"],
                "is_active": row["is_active"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

    async def create_bot_content(self, content_data) -> Dict[str, Any]:
        """Создать новый контент бота"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO bot_content (content_key, content_text, language, is_active)
                VALUES ($1, $2, $3, TRUE)
                RETURNING id, content_key, content_text, language, is_active, created_at, updated_at
                """,
                content_data.content_key,
                content_data.content_text,
                content_data.language,
            )

            return {
                "id": row["id"],
                "content_key": row["content_key"],
                "content_text": row["content_text"],
                "language": row["language"],
                "is_active": row["is_active"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

    async def update_bot_content_admin(self, content_key: str, language: str, content_data) -> Optional[Dict[str, Any]]:
        """Обновить контент бота (административная функция)"""
        async with self.pool.acquire() as conn:
            # Проверяем, существует ли контент
            existing = await conn.fetchrow(
                "SELECT id FROM bot_content WHERE content_key = $1 AND language = $2", content_key, language
            )

            if not existing:
                return None

            # Обновляем только указанные поля
            update_fields = []
            params = []
            param_count = 2

            if content_data.content_text is not None:
                update_fields.append(f"content_text = ${param_count + 1}")
                params.append(content_data.content_text)
                param_count += 1

            if content_data.is_active is not None:
                update_fields.append(f"is_active = ${param_count + 1}")
                params.append(content_data.is_active)
                param_count += 1

            if not update_fields:
                return None

            update_fields.append("updated_at = CURRENT_TIMESTAMP")

            query = f"""
                UPDATE bot_content 
                SET {', '.join(update_fields)}
                WHERE content_key = $1 AND language = $2
                RETURNING id, content_key, content_text, language, is_active, created_at, updated_at
            """

            params = [content_key, language] + params
            row = await conn.fetchrow(query, *params)

            return {
                "id": row["id"],
                "content_key": row["content_key"],
                "content_text": row["content_text"],
                "language": row["language"],
                "is_active": row["is_active"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

    async def deactivate_bot_content(self, content_key: str, language: str = "ru") -> bool:
        """Деактивировать контент бота"""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE bot_content SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP WHERE content_key = $1 AND language = $2",
                content_key,
                language,
            )
            return result != "UPDATE 0"

    async def activate_bot_content(self, content_key: str, language: str = "ru") -> bool:
        """Активировать контент бота"""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE bot_content SET is_active = TRUE, updated_at = CURRENT_TIMESTAMP WHERE content_key = $1 AND language = $2",
                content_key,
                language,
            )
            return result != "UPDATE 0"

    async def search_bot_content(self, query: str, language: str = None) -> List[Dict[str, Any]]:
        """Поиск контента бота по тексту"""
        async with self.pool.acquire() as conn:
            search_query = "SELECT id, content_key, content_text, language, is_active, created_at, updated_at FROM bot_content WHERE content_text ILIKE $1"
            params = [f"%{query}%"]

            if language:
                search_query += " AND language = $2"
                params.append(language)

            search_query += " ORDER BY content_key, language"

            rows = await conn.fetch(search_query, *params)

            content_list = []
            for row in rows:
                content_list.append(
                    {
                        "id": row["id"],
                        "content_key": row["content_key"],
                        "content_text": row["content_text"],
                        "language": row["language"],
                        "is_active": row["is_active"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    }
                )

            return content_list

    # Вспомогательные методы
    async def get_week_info(self, week_type: str) -> Dict[str, Any]:
        """Получить информацию о неделе (текущей или следующей)"""
        today = date.today()

        if week_type == "current":
            # Находим начало текущей недели (понедельник)
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday)
        else:  # next
            # Находим начало следующей недели
            days_since_monday = today.weekday()
            week_start = today - timedelta(days=days_since_monday) + timedelta(days=7)

        week_end = week_start + timedelta(days=6)

        return {
            "week_start_date": week_start,
            "week_end_date": week_end,
            "is_current": week_type == "current",
            "registration_deadline": datetime.combine(week_start, datetime.min.time()),
        }

    async def can_user_register_again(self, user_id: UUID) -> bool:
        """Проверить, может ли пользователь зарегистрироваться снова"""
        async with self.pool.acquire() as conn:
            # Проверяем, есть ли предыдущие регистрации
            has_previous = await conn.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM week_registrations 
                    WHERE user_id = $1 AND created_at < CURRENT_DATE
                )
                """,
                user_id,
            )

            if not has_previous:
                return True  # Первая регистрация всегда доступна

            # Получаем статистику пользователя
            user_stats = await conn.fetchrow(
                """
                SELECT total_sessions, feedback_count FROM users WHERE id = $1
                """,
                user_id,
            )

            if not user_stats:
                return False

            # Проверяем, что обратная связь дана по всем занятиям
            return user_stats["feedback_count"] >= user_stats["total_sessions"]

    # Методы для работы с настройками
    async def get_setting(self, key: str, default_value: str = None) -> Optional[str]:
        """Получить значение настройки"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT value FROM orator_settings
                WHERE key = $1 AND is_active = TRUE
                """,
                key,
            )
            return row["value"] if row else default_value

    async def get_setting_int(self, key: str, default_value: int = 0) -> int:
        """Получить значение настройки как целое число"""
        value = await self.get_setting(key)
        try:
            return int(value) if value else default_value
        except (ValueError, TypeError):
            return default_value

    async def get_setting_bool(self, key: str, default_value: bool = False) -> bool:
        """Получить значение настройки как булево значение"""
        value = await self.get_setting(key)
        if value is None:
            return default_value
        return value.lower() in ("true", "1", "yes", "on")

    async def update_setting(self, key: str, value: str, description: str = None) -> Optional[Dict[str, Any]]:
        """Обновить настройку"""
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                """
                INSERT INTO orator_settings (key, value, description, is_active)
                VALUES ($1, $2, $3, TRUE)
                ON CONFLICT (key) 
                DO UPDATE SET 
                    value = EXCLUDED.value,
                    description = COALESCE(EXCLUDED.description, orator_settings.description),
                    updated_at = CURRENT_TIMESTAMP
                """,
                key,
                value,
                description,
            )

            if result == "INSERT 0":
                return None

            # Возвращаем обновленную настройку
            row = await conn.fetchrow(
                """
                SELECT * FROM orator_settings WHERE key = $1
                """,
                key,
            )
            return dict(row) if row else None

    async def get_all_settings(self) -> List[Dict[str, Any]]:
        """Получить все настройки"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT key, value, description, is_active, created_at, updated_at
                FROM orator_settings
                ORDER BY key
                """
            )
            return [dict(row) for row in rows]

    async def add_message(self, message: MessageQueue) -> bool:
        """Добавить сообщение в очередь"""
        import json

        async with self.pool.acquire() as conn:
            # Сериализуем клавиатуру в JSON строку
            keyboard_json = json.dumps(message.keyboard) if message.keyboard else None

            result = await conn.execute(
                """
                INSERT INTO message_queue (user_id, message, keyboard, sent)
                VALUES ($1, $2, $3, $4)
                """,
                message.user_id,
                message.message,
                keyboard_json,
                message.sent,
            )
            return result != "INSERT 0"


# Создание экземпляра сервиса
orator_db = OratorDatabaseService()
