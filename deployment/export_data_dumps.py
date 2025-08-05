#!/usr/bin/env python3
"""
Скрипт для экспорта данных таблиц bot_content и topics в SQL дампы
"""

import asyncio
import asyncpg
import sys
import os
from datetime import datetime
from loguru import logger

# Добавляем путь к backend модулям
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

try:
    from config.settings import settings
except ImportError:
    # Fallback configuration
    DATABASE_URL = os.getenv("APP_DATABASE_URL", "postgresql://alex_orator:secure_password@localhost:5432/app_db")
    logger.warning("Using fallback database configuration")

    class FallbackSettings:
        @property
        def app_database_url(self):
            return DATABASE_URL

    settings = FallbackSettings()


class DataExporter:
    def __init__(self):
        self.database_url = settings.app_database_url
        self.pool = None

    async def connect(self):
        """Подключение к базе данных"""
        try:
            self.pool = await asyncpg.create_pool(self.database_url)
            logger.info("Connected to database for export")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def disconnect(self):
        """Отключение от базы данных"""
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from database")

    async def export_bot_content(self):
        """Экспорт данных таблицы bot_content"""
        logger.info("Exporting bot_content table...")

        async with self.pool.acquire() as conn:
            # Проверяем существование таблицы
            table_exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'bot_content')"
            )

            if not table_exists:
                logger.warning("Table bot_content does not exist")
                return ""

            # Получаем данные
            rows = await conn.fetch("SELECT * FROM bot_content ORDER BY content_key")

            if not rows:
                logger.warning("No data found in bot_content table")
                return ""

            # Генерируем SQL
            sql_lines = [
                "-- Alex Orator Bot - Bot Content Data",
                f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "-- Очистка существующих данных",
                "DELETE FROM bot_content;",
                "",
                "-- Вставка данных bot_content",
                "INSERT INTO bot_content (id, content_key, content_text, language, is_active, created_at, updated_at) VALUES",
            ]

            values = []
            for row in rows:
                # Экранируем текст для SQL
                content_text = row["content_text"].replace("'", "''")
                values.append(
                    f"('{row['id']}', '{row['content_key']}', '{content_text}', "
                    f"'{row['language']}', {str(row['is_active']).lower()}, "
                    f"'{row['created_at']}', '{row['updated_at']}')"
                )

            sql_lines.append(",\n".join(values) + ";")
            sql_lines.extend(
                [
                    "",
                    "-- Сброс последовательности AUTO_INCREMENT (если есть)",
                    "-- ALTER SEQUENCE bot_content_id_seq RESTART WITH 1;",
                    "",
                ]
            )

            logger.info(f"Exported {len(rows)} rows from bot_content")
            return "\n".join(sql_lines)

    async def export_topics(self):
        """Экспорт данных таблицы topics"""
        logger.info("Exporting topics table...")

        async with self.pool.acquire() as conn:
            # Проверяем существование таблицы
            table_exists = await conn.fetchval(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'topics')"
            )

            if not table_exists:
                logger.warning("Table topics does not exist")
                return ""

            # Получаем данные с правильной сортировкой (сначала родители, потом дети)
            rows = await conn.fetch(
                """
                WITH RECURSIVE topic_hierarchy AS (
                    -- Корневые темы (без родителей)
                    SELECT *, 0 as depth
                    FROM topics 
                    WHERE parent_id IS NULL
                    
                    UNION ALL
                    
                    -- Дочерние темы
                    SELECT t.*, th.depth + 1
                    FROM topics t
                    INNER JOIN topic_hierarchy th ON t.parent_id = th.id
                )
                SELECT * FROM topic_hierarchy 
                ORDER BY depth, sort_order, topic_id
            """
            )

            if not rows:
                logger.warning("No data found in topics table")
                return ""

            # Генерируем SQL
            sql_lines = [
                "-- Alex Orator Bot - Topics Data",
                f"-- Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "-- Очистка существующих данных",
                "DELETE FROM topics;",
                "",
                "-- Вставка данных topics",
                "INSERT INTO topics (id, topic_id, name, description, parent_id, level, sort_order, is_active, created_at, updated_at) VALUES",
            ]

            values = []
            for row in rows:
                # Экранируем текст для SQL
                name = row["name"].replace("'", "''") if row["name"] else ""
                description = row["description"].replace("'", "''") if row["description"] else ""
                parent_id = f"'{row['parent_id']}'" if row["parent_id"] else "NULL"

                values.append(
                    f"('{row['id']}', '{row['topic_id']}', '{name}', "
                    f"'{description}', {parent_id}, {row['level']}, "
                    f"{row['sort_order']}, {str(row['is_active']).lower()}, "
                    f"'{row['created_at']}', '{row['updated_at']}')"
                )

            sql_lines.append(",\n".join(values) + ";")
            sql_lines.extend(
                [
                    "",
                    "-- Сброс последовательности AUTO_INCREMENT (если есть)",
                    "-- ALTER SEQUENCE topics_id_seq RESTART WITH 1;",
                    "",
                ]
            )

            logger.info(f"Exported {len(rows)} rows from topics")
            return "\n".join(sql_lines)

    async def save_dump_to_file(self, filename: str, content: str):
        """Сохранение дампа в файл"""
        if not content.strip():
            logger.warning(f"No content to save for {filename}")
            return

        filepath = os.path.join(os.path.dirname(__file__), filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Dump saved to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save dump to {filepath}: {e}")
            raise

    async def export_all(self):
        """Экспорт всех таблиц"""
        logger.info("Starting data export...")

        await self.connect()

        try:
            # Экспорт bot_content
            bot_content_sql = await self.export_bot_content()
            if bot_content_sql:
                await self.save_dump_to_file("bot_content_dump.sql", bot_content_sql)

            # Экспорт topics
            topics_sql = await self.export_topics()
            if topics_sql:
                await self.save_dump_to_file("topics_dump.sql", topics_sql)

            logger.info("✅ Data export completed successfully!")

        finally:
            await self.disconnect()


async def main():
    """Главная функция"""
    logger.info("🚀 Alex Orator Bot - Data Export Tool")

    exporter = DataExporter()

    try:
        await exporter.export_all()
    except Exception as e:
        logger.error(f"Export failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
