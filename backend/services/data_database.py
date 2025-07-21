import asyncpg
from typing import List, Dict, Any, Optional
from loguru import logger
import time

from config.settings import settings
from models.database import TableInfo, ColumnInfo, DatabaseSchema


class DataDatabaseService:
    def __init__(self):
        self.database_url = settings.data_database_url
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Подключение к базе данных"""
        try:
            self.pool = await asyncpg.create_pool(self.database_url)
            logger.info("Connected to data database")
        except Exception as e:
            logger.error(f"Failed to connect to data database: {e}")
            raise

    async def disconnect(self):
        """Отключение от базы данных"""
        if self.pool:
            await self.pool.close()
            logger.info("Disconnected from data database")

    async def check_connection(self):
        """Проверка подключения к базе данных"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
        except Exception as e:
            logger.error(f"Data database connection check failed: {e}")
            raise

    async def get_tables(self) -> List[TableInfo]:
        """Получение списка таблиц"""
        async with self.pool.acquire() as conn:
            # Получаем список таблиц
            tables_query = """
                SELECT 
                    table_name,
                    (SELECT COUNT(*) FROM information_schema.columns 
                     WHERE table_name = t.table_name) as column_count
                FROM information_schema.tables t
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """

            rows = await conn.fetch(tables_query)
            tables = []

            for row in rows:
                # Получаем количество строк в таблице
                count_query = f"SELECT COUNT(*) as count FROM {row['table_name']}"
                count_result = await conn.fetchval(count_query)

                table_info = TableInfo(
                    name=row["table_name"], description=None, row_count=count_result  # TODO: получить из базы описаний
                )
                tables.append(table_info)

            return tables

    async def get_table_columns(self, table_name: str) -> List[ColumnInfo]:
        """Получение информации о колонках таблицы"""
        async with self.pool.acquire() as conn:
            columns_query = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_name = $1
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """

            rows = await conn.fetch(columns_query, table_name)
            columns = []

            for row in rows:
                column_info = ColumnInfo(
                    name=row["column_name"],
                    data_type=row["data_type"],
                    is_nullable=row["is_nullable"] == "YES",
                    description=None,  # TODO: получить из базы описаний
                )
                columns.append(column_info)

            return columns

    async def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """Выполнение SQL запроса (только SELECT)"""
        if not sql.strip().upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")

        start_time = time.time()

        async with self.pool.acquire() as conn:
            try:
                # Выполняем запрос
                rows = await conn.fetch(sql)

                # Конвертируем в список словарей
                result = []
                for row in rows:
                    result.append(dict(row))

                execution_time = time.time() - start_time
                logger.info(f"Query executed in {execution_time:.3f}s: {sql[:100]}...")

                return result

            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                raise

    async def get_sample_data(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение примера данных из таблицы"""
        sql = f"SELECT * FROM {table_name} LIMIT {limit}"
        return await self.execute_query(sql)

    async def get_database_schema(self) -> DatabaseSchema:
        """Получение полной схемы базы данных"""
        tables = await self.get_tables()
        table_columns = {}

        for table in tables:
            columns = await self.get_table_columns(table.name)
            table_columns[table.name] = columns

        return DatabaseSchema(tables=tables, table_columns=table_columns)

    async def validate_table_name(self, table_name: str) -> bool:
        """Проверка существования таблицы"""
        async with self.pool.acquire() as conn:
            query = """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = $1 AND table_schema = 'public'
                )
            """
            return await conn.fetchval(query, table_name)

    async def get_table_row_count(self, table_name: str) -> int:
        """Получение количества строк в таблице"""
        async with self.pool.acquire() as conn:
            query = f"SELECT COUNT(*) FROM {table_name}"
            return await conn.fetchval(query)


# Создание экземпляра сервиса
data_database_service = DataDatabaseService()
