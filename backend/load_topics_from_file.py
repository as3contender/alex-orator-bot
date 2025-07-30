#!/usr/bin/env python3
"""
Скрипт для загрузки тем из файла topics.txt в таблицу topics
"""

import asyncio
import asyncpg
from loguru import logger
import os
from collections import defaultdict

# Настройки базы данных
DATABASE_URL = os.getenv("APP_DATABASE_URL", "postgresql://alex_orator:your_password@localhost:5434/app_db")


class TopicsLoader:
    def __init__(self):
        self.conn = None
        self.topics_data = []
        self.hierarchy = defaultdict(set)  # topic -> levels
        self.level_tasks = defaultdict(lambda: defaultdict(set))  # topic -> level -> tasks

    async def connect(self):
        """Подключение к базе данных"""
        try:
            self.conn = await asyncpg.connect(DATABASE_URL)
            logger.info("Connected to database successfully")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def disconnect(self):
        """Отключение от базы данных"""
        if self.conn:
            await self.conn.close()
            logger.info("Disconnected from database")

    def parse_topics_file(self, file_path: str):
        """Парсинг файла topics.txt"""
        logger.info(f"Parsing topics file: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        # Формат: topic_id \t topic_name \t level \t task
                        parts = line.split("\t")
                        if len(parts) != 4:
                            logger.warning(f"Line {line_num}: Invalid format, expected 4 parts, got {len(parts)}")
                            continue

                        topic_id, topic_name, level, task = parts

                        # Сохраняем данные
                        self.topics_data.append(
                            {"topic_id": topic_id, "topic_name": topic_name, "level": level, "task": task}
                        )

                        # Строим иерархию
                        self.hierarchy[topic_name].add(level)
                        self.level_tasks[topic_name][level].add(task)

                    except Exception as e:
                        logger.error(f"Error parsing line {line_num}: {e}")
                        continue

            logger.info(f"Parsed {len(self.topics_data)} topic entries")
            logger.info(f"Found {len(self.hierarchy)} unique topics")

            # Показываем структуру
            for topic, levels in self.hierarchy.items():
                logger.info(f"Topic '{topic}' has levels: {sorted(levels)}")
                for level in sorted(levels):
                    tasks = self.level_tasks[topic][level]
                    logger.info(f"  Level '{level}' has tasks: {sorted(tasks)}")

        except Exception as e:
            logger.error(f"Failed to parse topics file: {e}")
            raise

    async def clear_existing_topics(self):
        """Очистка существующих тем (опционально)"""
        try:
            result = await self.conn.execute("DELETE FROM topics")
            logger.info(f"Cleared existing topics. Deleted rows: {result}")
        except Exception as e:
            logger.error(f"Failed to clear existing topics: {e}")
            raise

    async def load_topics_to_database(self):
        """Загрузка тем в базу данных с созданием иерархии"""
        logger.info("Loading topics to database...")

        try:
            # Словарь для хранения UUID родительских элементов
            parent_uuids = {}
            sort_order = 0

            # 1. Создаем корневые темы
            for topic_name in sorted(self.hierarchy.keys()):
                sort_order += 1

                # Создаем topic_id для корневой темы (убираем пробелы и приводим к нижнему регистру)
                root_topic_id = topic_name.replace(" ", "_").lower()

                # Вставляем корневую тему
                root_uuid = await self.conn.fetchval(
                    """
                    INSERT INTO topics (topic_id, name, description, parent_id, level, sort_order, is_active)
                    VALUES ($1, $2, $3, NULL, 1, $4, TRUE)
                    ON CONFLICT (topic_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        sort_order = EXCLUDED.sort_order,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                    """,
                    root_topic_id,
                    topic_name.title(),
                    f"Тема: {topic_name.title()}",
                    sort_order,
                )

                parent_uuids[root_topic_id] = root_uuid
                logger.info(f"Created root topic: {topic_name} (ID: {root_topic_id}, UUID: {root_uuid})")

                # 2. Создаем уровни для каждой темы
                levels = sorted(self.hierarchy[topic_name])
                for level_order, level in enumerate(levels, 1):
                    level_topic_id = f"{root_topic_id}_{level}"
                    level_name = f"{topic_name.title()} - {level.title()}"

                    level_uuid = await self.conn.fetchval(
                        """
                        INSERT INTO topics (topic_id, name, description, parent_id, level, sort_order, is_active)
                        VALUES ($1, $2, $3, $4, 2, $5, TRUE)
                        ON CONFLICT (topic_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            parent_id = EXCLUDED.parent_id,
                            sort_order = EXCLUDED.sort_order,
                            updated_at = CURRENT_TIMESTAMP
                        RETURNING id
                        """,
                        level_topic_id,
                        level_name,
                        f"Уровень {level.title()} для темы {topic_name.title()}",
                        root_uuid,
                        level_order,
                    )

                    parent_uuids[level_topic_id] = level_uuid
                    logger.info(f"  Created level: {level_name} (ID: {level_topic_id}, UUID: {level_uuid})")

                    # 3. Создаем задания для каждого уровня
                    tasks = sorted(self.level_tasks[topic_name][level])
                    for task_order, task in enumerate(tasks, 1):
                        task_topic_id = f"{level_topic_id}_{task}"
                        task_name = f"{topic_name.title()} - {level.title()} - {task.title()}"

                        task_uuid = await self.conn.fetchval(
                            """
                            INSERT INTO topics (topic_id, name, description, parent_id, level, sort_order, is_active)
                            VALUES ($1, $2, $3, $4, 3, $5, TRUE)
                            ON CONFLICT (topic_id) DO UPDATE SET
                                name = EXCLUDED.name,
                                parent_id = EXCLUDED.parent_id,
                                sort_order = EXCLUDED.sort_order,
                                updated_at = CURRENT_TIMESTAMP
                            RETURNING id
                            """,
                            task_topic_id,
                            task_name,
                            f"Задание {task.title()} для уровня {level.title()} темы {topic_name.title()}",
                            level_uuid,
                            task_order,
                        )

                        logger.info(f"    Created task: {task_name} (ID: {task_topic_id}, UUID: {task_uuid})")

            logger.info("Successfully loaded all topics to database")

        except Exception as e:
            logger.error(f"Failed to load topics to database: {e}")
            raise

    async def verify_topics(self):
        """Проверка загруженных тем"""
        try:
            # Подсчет по уровням
            level_counts = await self.conn.fetch(
                "SELECT level, COUNT(*) as count FROM topics GROUP BY level ORDER BY level"
            )

            logger.info("Topics verification:")
            for row in level_counts:
                logger.info(f"  Level {row['level']}: {row['count']} topics")

            # Показать несколько примеров
            examples = await self.conn.fetch(
                """
                SELECT topic_id, name, level, 
                       (SELECT name FROM topics p WHERE p.id = t.parent_id) as parent_name
                FROM topics t 
                ORDER BY level, sort_order 
                LIMIT 10
                """
            )

            logger.info("Examples of loaded topics:")
            for example in examples:
                parent_info = f" (parent: {example['parent_name']})" if example["parent_name"] else ""
                logger.info(f"  Level {example['level']}: {example['name']} (ID: {example['topic_id']}){parent_info}")

        except Exception as e:
            logger.error(f"Failed to verify topics: {e}")
            raise

    async def run(self, topics_file_path: str, clear_existing: bool = False):
        """Основной метод запуска"""
        try:
            await self.connect()

            # Парсим файл
            self.parse_topics_file(topics_file_path)

            if clear_existing:
                logger.info("Clearing existing topics...")
                await self.clear_existing_topics()

            # Загружаем в базу данных
            await self.load_topics_to_database()

            # Проверяем результат
            await self.verify_topics()

            logger.info("Topics loading completed successfully!")

        except Exception as e:
            logger.error(f"Topics loading failed: {e}")
            raise
        finally:
            await self.disconnect()


async def main():
    """Главная функция"""
    logger.info("Starting topics loading from file...")

    # Путь к файлу topics.txt
    topics_file = "texts/topics.txt"

    if not os.path.exists(topics_file):
        logger.error(f"Topics file not found: {topics_file}")
        return

    loader = TopicsLoader()

    # Спросим пользователя, нужно ли очищать существующие темы
    clear_existing = input("Clear existing topics? (y/N): ").strip().lower() == "y"

    await loader.run(topics_file, clear_existing=clear_existing)


if __name__ == "__main__":
    asyncio.run(main())
