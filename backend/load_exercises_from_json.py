import asyncio
import asyncpg
import json
import os
from loguru import logger


class ExercisesJsonLoader:
    """Класс для загрузки упражнений из JSON файла в таблицу bot_content"""

    def __init__(self):
        self.conn = None
        self.exercises_data = []

    async def connect_to_db(self):
        """Подключение к базе данных"""
        try:
            database_url = os.getenv("APP_DATABASE_URL")
            if not database_url:
                raise ValueError("APP_DATABASE_URL environment variable is not set")

            self.conn = await asyncpg.connect(database_url)
            logger.info("Connected to database successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def load_json_file(self, file_path: str):
        """Загрузка JSON файла с упражнениями"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.exercises_data = json.load(f)
            logger.info(f"Loaded exercises JSON data from {file_path}")
            logger.info(f"Found {len(self.exercises_data)} exercises")
        except Exception as e:
            logger.error(f"Failed to load JSON file: {e}")
            raise

    async def clear_existing_exercises(self):
        """Очистка существующих упражнений (только с префиксом exercise_)"""
        try:
            # Удаляем только записи с content_key, начинающимся на 'exercise_'
            result = await self.conn.execute("DELETE FROM bot_content WHERE content_key LIKE 'exercise_%'")
            logger.info(f"Cleared existing exercises from database: {result}")
        except Exception as e:
            logger.error(f"Failed to clear existing exercises: {e}")
            raise

    async def load_exercises_to_database(self):
        """Загрузка упражнений в базу данных"""
        logger.info("Loading exercises to database...")

        success_count = 0
        error_count = 0

        for exercise in self.exercises_data:
            try:
                content_key = exercise.get("content_key", "")
                content_text = exercise.get("content_text", "")

                if not content_key or not content_text:
                    logger.warning(f"Skipping exercise with empty content_key or content_text")
                    error_count += 1
                    continue

                # Вставляем упражнение в bot_content
                await self.conn.execute(
                    """
                    INSERT INTO bot_content (content_key, content_text, language, is_active)
                    VALUES ($1, $2, 'ru', TRUE)
                    ON CONFLICT (content_key, language) DO UPDATE SET
                        content_text = EXCLUDED.content_text,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    content_key,
                    content_text,
                )

                logger.info(f"Inserted exercise: {content_key}")
                success_count += 1

            except Exception as e:
                logger.error(f"Failed to insert exercise {content_key}: {e}")
                error_count += 1

        logger.info(f"Exercise loading completed: {success_count} success, {error_count} errors")

    async def verify_loaded_data(self):
        """Проверка загруженных данных"""
        logger.info("Verifying loaded exercises...")

        # Подсчитываем количество упражнений
        count = await self.conn.fetchval("SELECT COUNT(*) FROM bot_content WHERE content_key LIKE 'exercise_%'")
        logger.info(f"Total exercises loaded: {count}")

        # Показываем примеры по темам
        logger.info("Sample exercises by topic:")

        # Группируем по префиксам topic_id (первые 2 цифры)
        samples = await self.conn.fetch(
            """
            SELECT content_key, LEFT(content_text, 60) as preview
            FROM bot_content 
            WHERE content_key LIKE 'exercise_%'
            ORDER BY content_key
            LIMIT 10
        """
        )

        for sample in samples:
            logger.info(f"  {sample['content_key']} | {sample['preview']}...")

        # Статистика по темам
        topic_stats = await self.conn.fetch(
            """
            SELECT 
                SUBSTRING(content_key FROM 'exercise_(..)') as topic_prefix,
                COUNT(*) as count
            FROM bot_content 
            WHERE content_key LIKE 'exercise_%'
            GROUP BY SUBSTRING(content_key FROM 'exercise_(..)')
            ORDER BY topic_prefix
        """
        )

        logger.info("Exercises by topic:")
        for stat in topic_stats:
            topic_map = {
                "01": "Речевая Импровизация",
                "02": "Четкость И Плавность Речи",
                "03": "Контакт с аудиторией",
                "04": "Эмоции",
                "05": "Сторителлинг",
                "06": "Структура",
            }
            topic_name = topic_map.get(stat["topic_prefix"], f"Topic {stat['topic_prefix']}")
            logger.info(f"  {stat['topic_prefix']} ({topic_name}): {stat['count']} exercises")

    async def close_connection(self):
        """Закрытие соединения с БД"""
        if self.conn:
            await self.conn.close()
            logger.info("Database connection closed")

    async def run(self, json_file_path: str):
        """Основной метод выполнения"""
        try:
            await self.connect_to_db()
            await self.load_json_file(json_file_path)
            await self.clear_existing_exercises()
            await self.load_exercises_to_database()
            await self.verify_loaded_data()
            logger.success("Exercises loaded successfully!")

        except Exception as e:
            logger.error(f"Error during execution: {e}")
            raise
        finally:
            await self.close_connection()


async def main():
    """Главная функция"""
    json_file_path = "texts/exercises.json"
    loader = ExercisesJsonLoader()
    await loader.run(json_file_path)


if __name__ == "__main__":
    asyncio.run(main())
