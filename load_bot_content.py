#!/usr/bin/env python3
"""
Скрипт для загрузки контента бота в базу данных
"""

import asyncio
import asyncpg
from loguru import logger
import sys
import os

# Добавляем путь к модулям проекта
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from config.settings import settings
from content_parser import ContentParser


class ContentLoader:
    def __init__(self):
        self.database_url = settings.app_database_url
        self.pool = None
        self.parser = ContentParser()

    async def connect(self):
        """Подключение к базе данных"""
        try:
            self.pool = await asyncpg.create_pool(self.database_url)
            logger.info("Connected to database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def disconnect(self):
        """Отключение от базы данных"""
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from database")

    async def load_bot_messages(self):
        """Загрузка сообщений бота"""
        logger.info("Loading bot messages...")

        messages = self.parser.get_bot_messages()

        async with self.pool.acquire() as conn:
            for message_key, languages in messages.items():
                for language, text in languages.items():
                    try:
                        await conn.execute(
                            """
                            INSERT INTO bot_content (content_key, content_text, language, is_active)
                            VALUES ($1, $2, $3, TRUE)
                            ON CONFLICT (content_key, language) 
                            DO UPDATE SET 
                                content_text = EXCLUDED.content_text,
                                updated_at = CURRENT_TIMESTAMP
                            """,
                            message_key,
                            text,
                            language,
                        )
                        logger.info(f"Loaded message: {message_key} ({language})")
                    except Exception as e:
                        logger.error(f"Error loading message {message_key}: {e}")

    async def load_exercises(self):
        """Загрузка упражнений"""
        logger.info("Loading exercises...")

        exercises = self.parser.get_exercises()

        async with self.pool.acquire() as conn:
            for exercise_key, languages in exercises.items():
                for language, text in languages.items():
                    try:
                        await conn.execute(
                            """
                            INSERT INTO bot_content (content_key, content_text, language, is_active)
                            VALUES ($1, $2, $3, TRUE)
                            ON CONFLICT (content_key, language) 
                            DO UPDATE SET 
                                content_text = EXCLUDED.content_text,
                                updated_at = CURRENT_TIMESTAMP
                            """,
                            f"exercise_{exercise_key}",
                            text,
                            language,
                        )
                        logger.info(f"Loaded exercise: {exercise_key} ({language})")
                    except Exception as e:
                        logger.error(f"Error loading exercise {exercise_key}: {e}")

    async def load_topics(self):
        """Загрузка тем"""
        logger.info("Loading topics...")

        topics = self.parser.get_topics()

        async with self.pool.acquire() as conn:
            # Сначала загружаем родительские темы
            for topic in topics:
                if "parent_id" not in topic:
                    try:
                        await conn.execute(
                            """
                            INSERT INTO topics (topic_id, name, level, sort_order, is_active)
                            VALUES ($1, $2, $3, $4, TRUE)
                            ON CONFLICT (topic_id) 
                            DO UPDATE SET 
                                name = EXCLUDED.name,
                                level = EXCLUDED.level,
                                sort_order = EXCLUDED.sort_order,
                                updated_at = CURRENT_TIMESTAMP
                            """,
                            topic["topic_id"],
                            topic["name"],
                            topic["level"],
                            topic["sort_order"],
                        )
                        logger.info(f"Loaded parent topic: {topic['name']}")
                    except Exception as e:
                        logger.error(f"Error loading parent topic {topic['topic_id']}: {e}")

            # Затем загружаем дочерние темы
            for topic in topics:
                if "parent_id" in topic:
                    try:
                        # Получаем ID родительской темы
                        parent_id = await conn.fetchval("SELECT id FROM topics WHERE topic_id = $1", topic["parent_id"])

                        if parent_id:
                            await conn.execute(
                                """
                                INSERT INTO topics (topic_id, name, parent_id, level, sort_order, is_active)
                                VALUES ($1, $2, $3, $4, $5, TRUE)
                                ON CONFLICT (topic_id) 
                                DO UPDATE SET 
                                    name = EXCLUDED.name,
                                    parent_id = EXCLUDED.parent_id,
                                    level = EXCLUDED.level,
                                    sort_order = EXCLUDED.sort_order,
                                    updated_at = CURRENT_TIMESTAMP
                                """,
                                topic["topic_id"],
                                topic["name"],
                                parent_id,
                                topic["level"],
                                topic["sort_order"],
                            )
                            logger.info(f"Loaded child topic: {topic['name']}")
                        else:
                            logger.warning(f"Parent topic {topic['parent_id']} not found for {topic['topic_id']}")
                    except Exception as e:
                        logger.error(f"Error loading child topic {topic['topic_id']}: {e}")

    async def verify_content(self):
        """Проверка загруженного контента"""
        logger.info("Verifying loaded content...")

        async with self.pool.acquire() as conn:
            # Проверяем сообщения
            messages_count = await conn.fetchval(
                "SELECT COUNT(*) FROM bot_content WHERE content_key IN ('приветственное_сообщение', 'хочешь_тренироваться_на_этой_неделе_второе_сообщение', 'обратная_связь_для_регистрации_на_следующую_неделю')"
            )
            logger.info(f"Loaded {messages_count} bot messages")

            # Проверяем упражнения
            exercises_count = await conn.fetchval(
                "SELECT COUNT(*) FROM bot_content WHERE content_key LIKE 'exercise_%'"
            )
            logger.info(f"Loaded {exercises_count} exercises")

            # Проверяем темы
            topics_count = await conn.fetchval("SELECT COUNT(*) FROM topics")
            logger.info(f"Loaded {topics_count} topics")

            # Показываем примеры загруженного контента
            sample_messages = await conn.fetch(
                "SELECT content_key, content_text FROM bot_content WHERE content_key IN ('приветственное_сообщение', 'хочешь_тренироваться_на_этой_неделе_второе_сообщение') LIMIT 2"
            )
            logger.info("Sample messages loaded:")
            for msg in sample_messages:
                logger.info(f"  {msg['content_key']}: {msg['content_text'][:100]}...")

            sample_exercises = await conn.fetch(
                "SELECT content_key, content_text FROM bot_content WHERE content_key LIKE 'exercise_%' LIMIT 2"
            )
            logger.info("Sample exercises loaded:")
            for exercise in sample_exercises:
                logger.info(f"  {exercise['content_key']}: {exercise['content_text'][:100]}...")

            sample_topics = await conn.fetch(
                "SELECT name, level FROM topics WHERE level = 1 ORDER BY sort_order LIMIT 3"
            )
            logger.info("Sample topics loaded:")
            for topic in sample_topics:
                logger.info(f"  {topic['name']} (level {topic['level']})")

    async def run(self):
        """Запуск загрузки контента"""
        try:
            await self.connect()

            logger.info("Starting content loading...")

            # Парсим контент из файлов
            bot_messages_path = "texts/bot_messages.txt"
            exercises_path = "texts/exercises.txt"

            logger.info("Parsing content from files...")
            self.parser.parse_all_content(bot_messages_path, exercises_path)

            # Загружаем контент
            await self.load_bot_messages()
            await self.load_exercises()
            await self.load_topics()

            # Проверяем результат
            await self.verify_content()

            logger.info("✅ Content loading completed successfully!")

        except Exception as e:
            logger.error(f"Error during content loading: {e}")
            raise
        finally:
            await self.disconnect()


async def main():
    """Главная функция"""
    loader = ContentLoader()
    await loader.run()


if __name__ == "__main__":
    asyncio.run(main())
