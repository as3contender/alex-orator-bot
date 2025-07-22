import asyncpg
from typing import Optional, List, Dict, Any
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
            await self._create_orator_tables()
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
                    to_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
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

            # Инициализация базового контента
            await self._initialize_bot_content(conn)

            # Инициализация настроек по умолчанию
            await self._initialize_default_settings(conn)

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
                    WHERE user_id = $1 AND status = 'active'
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
    async def create_user_pair(self, user1_id: UUID, user2_id: UUID, registration_id: UUID) -> UUID:
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
            # Возвращаем созданную пару
            row = await conn.fetchrow(
                """
                SELECT * FROM user_pairs WHERE id = $1
                """,
                pair_id,
            )
            return dict(row) if row else None

    async def confirm_user_pair(self, pair_id: UUID, confirmed: bool) -> Optional[Dict[str, Any]]:
        """Подтвердить или отклонить пару"""
        async with self.pool.acquire() as conn:
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
                SELECT * FROM user_pairs WHERE id = $1
                """,
                pair_id,
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
                        WHEN up.user1_id = $1 THEN u2.first_name || ' ' || COALESCE(u2.last_name, '')
                        ELSE u1.first_name || ' ' || COALESCE(u1.last_name, '')
                    END as partner_name,
                    wr.week_start_date, wr.week_end_date
                FROM user_pairs up
                JOIN week_registrations wr ON up.week_registration_id = wr.id
                JOIN users u1 ON up.user1_id = u1.id
                JOIN users u2 ON up.user2_id = u2.id
                WHERE (up.user1_id = $1 OR up.user2_id = $1) 
                AND wr.week_start_date = $2
                ORDER BY up.created_at DESC
                """,
                user_id,
                week_start,
            )
            return [dict(row) for row in rows]

    # Методы для работы с обратной связью
    async def create_session_feedback(
        self, pair_id: UUID, from_user_id: UUID, to_user_id: UUID, feedback_text: str, rating: int
    ) -> UUID:
        """Создать обратную связь по занятию"""
        async with self.pool.acquire() as conn:
            feedback_id = await conn.fetchval(
                """
                INSERT INTO session_feedback 
                (pair_id, from_user_id, to_user_id, feedback_text, rating)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
                """,
                pair_id,
                from_user_id,
                to_user_id,
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
                # Получить данную обратную связь
                rows = await conn.fetch(
                    """
                    SELECT 
                        sf.id, sf.pair_id, sf.feedback_text, sf.rating, sf.created_at,
                        u.first_name || ' ' || COALESCE(u.last_name, '') as to_user_name
                    FROM session_feedback sf
                    JOIN users u ON sf.to_user_id = u.id
                    WHERE sf.from_user_id = $1
                    ORDER BY sf.created_at DESC
                    """,
                    from_user_id,
                )
            elif to_user_id:
                # Получить полученную обратную связь
                rows = await conn.fetch(
                    """
                    SELECT 
                        sf.id, sf.pair_id, sf.feedback_text, sf.rating, sf.created_at,
                        u.first_name || ' ' || COALESCE(u.last_name, '') as from_user_name
                    FROM session_feedback sf
                    JOIN users u ON sf.from_user_id = u.id
                    WHERE sf.to_user_id = $1
                    ORDER BY sf.created_at DESC
                    """,
                    to_user_id,
                )
            else:
                return []

            return [dict(row) for row in rows]

    # Методы для работы с контентом
    async def get_topic_tree(self) -> Dict[str, Any]:
        """Получить дерево тем"""
        # TODO: Реализовать получение дерева тем из базы данных
        # Пока возвращаем статичную структуру
        return {
            "topics": [
                {
                    "id": "delivery",
                    "name": "Подача",
                    "children": [
                        {
                            "id": "speech-topics-1",
                            "name": "Темы речи уровень 1",
                            "path": "Подача - Темы речи уровень 1",
                        },
                        {
                            "id": "speech-topics-2",
                            "name": "Темы речи уровень 2",
                            "path": "Подача - Темы речи уровень 2",
                        },
                    ],
                },
                {
                    "id": "voice",
                    "name": "Голос",
                    "children": [
                        {"id": "intonation", "name": "Интонация", "path": "Голос - Интонация"},
                        {"id": "diction", "name": "Дикция", "path": "Голос - Дикция"},
                    ],
                },
                {
                    "id": "gestures",
                    "name": "Жесты",
                    "children": [
                        {"id": "basic-gestures", "name": "Базовые", "path": "Жесты - Базовые"},
                        {"id": "advanced-gestures", "name": "Продвинутые", "path": "Жесты - Продвинутые"},
                    ],
                },
            ]
        }

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


# Создание экземпляра сервиса
orator_db = OratorDatabaseService()
