import asyncio
import asyncpg
import json
import os
from loguru import logger


class BotMessagesJsonLoader:
    """Класс для загрузки сообщений бота из JSON файла в таблицу bot_content"""

    def __init__(self):
        self.conn = None
        self.messages_data = []

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
        """Загрузка JSON файла с сообщениями бота"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.messages_data = json.load(f)
            logger.info(f"Loaded bot messages JSON data from {file_path}")
            logger.info(f"Found {len(self.messages_data)} bot messages")
        except Exception as e:
            logger.error(f"Failed to load JSON file: {e}")
            raise

    async def clear_existing_messages(self):
        """Удаление существующих сообщений с такими же ключами"""
        try:
            # Получаем список всех content_key из JSON
            content_keys = [msg.get("content_key", "") for msg in self.messages_data if msg.get("content_key")]

            if not content_keys:
                logger.warning("No content_keys found in JSON file")
                return

            logger.info(f"Deleting existing messages with keys: {content_keys}")

            # Удаляем записи с этими ключами
            placeholders = ",".join([f"${i+1}" for i in range(len(content_keys))])
            query = f"DELETE FROM bot_content WHERE content_key IN ({placeholders})"

            result = await self.conn.execute(query, *content_keys)
            logger.info(f"Cleared existing bot messages from database: {result}")

        except Exception as e:
            logger.error(f"Failed to clear existing messages: {e}")
            raise

    async def load_messages_to_database(self):
        """Загрузка сообщений бота в базу данных"""
        logger.info("Loading bot messages to database...")

        success_count = 0
        error_count = 0

        for message in self.messages_data:
            try:
                content_key = message.get("content_key", "")
                content_text = message.get("content_text", "")

                if not content_key or not content_text:
                    logger.warning(f"Skipping message with empty content_key or content_text")
                    error_count += 1
                    continue

                # Вставляем сообщение в bot_content
                await self.conn.execute(
                    """
                    INSERT INTO bot_content (content_key, content_text, language, is_active)
                    VALUES ($1, $2, 'ru', TRUE)
                    """,
                    content_key,
                    content_text,
                )

                logger.info(f"Inserted bot message: {content_key}")
                success_count += 1

            except Exception as e:
                logger.error(f"Failed to insert message {content_key}: {e}")
                error_count += 1

        logger.info(f"Bot messages loading completed: {success_count} success, {error_count} errors")

    async def verify_loaded_data(self):
        """Проверка загруженных данных"""
        logger.info("Verifying loaded bot messages...")

        # Получаем список ключей из JSON для проверки
        expected_keys = [msg.get("content_key", "") for msg in self.messages_data if msg.get("content_key")]

        # Проверяем что все ключи загружены
        placeholders = ",".join([f"${i+1}" for i in range(len(expected_keys))])
        query = f"""
            SELECT content_key, LEFT(content_text, 80) as preview
            FROM bot_content 
            WHERE content_key IN ({placeholders})
            ORDER BY content_key
        """

        loaded_messages = await self.conn.fetch(query, *expected_keys)

        logger.info(f"Loaded {len(loaded_messages)} bot messages:")
        for msg in loaded_messages:
            logger.info(f"  {msg['content_key']:30} | {msg['preview']}...")

        # Проверяем что все ожидаемые ключи присутствуют
        loaded_keys = {msg["content_key"] for msg in loaded_messages}
        expected_keys_set = set(expected_keys)

        missing_keys = expected_keys_set - loaded_keys
        if missing_keys:
            logger.warning(f"Missing keys in database: {missing_keys}")
        else:
            logger.success("All bot messages loaded successfully!")

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
            await self.clear_existing_messages()
            await self.load_messages_to_database()
            await self.verify_loaded_data()
            logger.success("Bot messages loaded successfully!")

        except Exception as e:
            logger.error(f"Error during execution: {e}")
            raise
        finally:
            await self.close_connection()


async def main():
    """Главная функция"""
    json_file_path = "texts/bot_messages.json"
    loader = BotMessagesJsonLoader()
    await loader.run(json_file_path)


if __name__ == "__main__":
    asyncio.run(main())
