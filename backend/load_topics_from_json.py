import asyncio
import asyncpg
import json
import os
from loguru import logger


class TopicsJsonLoader:
    """Класс для загрузки тем из JSON файла в базу данных"""

    def __init__(self):
        self.conn = None
        self.hierarchy_data = []

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
        """Загрузка JSON файла"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.hierarchy_data = json.load(f)
            logger.info(f"Loaded JSON data from {file_path}")
            logger.info(f"Found {len(self.hierarchy_data)} top-level groups")
        except Exception as e:
            logger.error(f"Failed to load JSON file: {e}")
            raise

    async def clear_existing_topics(self):
        """Очистка существующих тем"""
        try:
            await self.conn.execute("DELETE FROM topics")
            logger.info("Cleared existing topics from database")
        except Exception as e:
            logger.error(f"Failed to clear existing topics: {e}")
            raise

    async def load_topics_to_database(self):
        """Загрузка тем в базу данных с созданием иерархии"""
        logger.info("Loading topics to database...")

        # Словарь для хранения UUID родительских элементов
        parent_uuids = {}

        # 1. Загружаем группы (level 1)
        for group_index, group in enumerate(self.hierarchy_data, 1):
            topic_id = group["topic_id"]
            name = group["name"]

            # Вставляем группу
            group_uuid = await self.conn.fetchval(
                """
                INSERT INTO topics (topic_id, name, description, parent_id, level, sort_order, is_active)
                VALUES ($1, $2, $3, NULL, 1, $4, TRUE)
                RETURNING id
                """,
                topic_id,
                name,
                f"Группа: {name}",
                group_index,
            )
            parent_uuids[topic_id] = group_uuid
            logger.info(f"Inserted group: {topic_id} -> {name}")

            # 2. Загружаем уровни (level 2)
            if "children" in group:
                for level_index, level in enumerate(group["children"], 1):
                    level_topic_id = level["topic_id"]
                    level_name = level["name"]

                    # Вставляем уровень
                    level_uuid = await self.conn.fetchval(
                        """
                        INSERT INTO topics (topic_id, name, description, parent_id, level, sort_order, is_active)
                        VALUES ($1, $2, $3, $4, 2, $5, TRUE)
                        RETURNING id
                        """,
                        level_topic_id,
                        level_name,
                        f"Уровень: {level_name}",
                        group_uuid,
                        level_index,
                    )
                    parent_uuids[level_topic_id] = level_uuid
                    logger.info(f"  Inserted level: {level_topic_id} -> {level_name}")

                    # 3. Загружаем задания (level 3)
                    if "children" in level:
                        for task_index, task in enumerate(level["children"], 1):
                            task_topic_id = task["topic_id"]
                            task_name = task["name"]

                            # Вставляем задание
                            await self.conn.execute(
                                """
                                INSERT INTO topics (topic_id, name, description, parent_id, level, sort_order, is_active)
                                VALUES ($1, $2, $3, $4, 3, $5, TRUE)
                                """,
                                task_topic_id,
                                task_name,
                                f"Задание: {task_name}",
                                level_uuid,
                                task_index,
                            )
                            logger.info(f"    Inserted task: {task_topic_id} -> {task_name}")

    async def verify_loaded_data(self):
        """Проверка загруженных данных"""
        logger.info("Verifying loaded data...")

        # Проверяем количество записей по уровням
        for level in [1, 2, 3]:
            count = await self.conn.fetchval("SELECT COUNT(*) FROM topics WHERE level = $1", level)
            logger.info(f"Level {level}: {count} topics")

        # Показываем несколько примеров
        logger.info("Sample data:")
        samples = await self.conn.fetch(
            """
            SELECT topic_id, name, level, 
                   (SELECT name FROM topics p WHERE p.id = t.parent_id) as parent_name
            FROM topics t 
            ORDER BY level, sort_order 
            LIMIT 10
        """
        )

        for sample in samples:
            parent_info = f" (parent: {sample['parent_name']})" if sample["parent_name"] else ""
            logger.info(f"  {sample['topic_id']} | Level {sample['level']} | {sample['name']}{parent_info}")

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
            await self.clear_existing_topics()
            await self.load_topics_to_database()
            await self.verify_loaded_data()
            logger.success("Topics loaded successfully!")

        except Exception as e:
            logger.error(f"Error during execution: {e}")
            raise
        finally:
            await self.close_connection()


async def main():
    """Главная функция"""
    json_file_path = "texts/topics.json"
    loader = TopicsJsonLoader()
    await loader.run(json_file_path)


if __name__ == "__main__":
    asyncio.run(main())
