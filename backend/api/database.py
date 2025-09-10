from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from typing import List, Dict, Any
import time
import asyncio

from models.database import QueryRequest, QueryResponse, TableInfo, ColumnInfo, SampleDataRequest, DatabaseSchema
from services.security import security_service
from services.app_database import app_database_service
from models.user_settings import UserSettings

router = APIRouter()


@router.get("/tables", response_model=List[TableInfo])
async def get_tables(current_user_id: str = Depends(security_service.get_current_user_id)):
    """Получить список доступных таблиц"""
    try:
        # Получаем список таблиц из базы данных
        async with app_database_service.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    table_name, 
                    (SELECT COUNT(*) FROM users) as row_count
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                AND table_name NOT LIKE 'pg_%'
                ORDER BY table_name
            """)
            
            tables = []
            for row in rows:
                table_info = TableInfo(
                    name=row['table_name'],
                    description=f"Таблица {row['table_name']}",
                    row_count=row['row_count'] if row['table_name'] == 'users' else None
                )
                tables.append(table_info)
            
            return tables
    except Exception as e:
        logger.error(f"Error getting tables: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get tables")


@router.get("/tables/{table_name}/columns", response_model=List[ColumnInfo])
async def get_table_columns(table_name: str, current_user_id: str = Depends(security_service.get_current_user_id)):
    """Получить информацию о колонках таблицы"""
    try:
        async with app_database_service.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_name = $1 
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """, table_name)
            
            columns = []
            for row in rows:
                column_info = ColumnInfo(
                    name=row['column_name'],
                    type=row['data_type'],
                    nullable=row['is_nullable'] == 'YES',
                    default=row['column_default'],
                    description=f"Колонка {row['column_name']}"
                )
                columns.append(column_info)
            
            return columns
    except Exception as e:
        logger.error(f"Error getting columns for table {table_name}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get table columns")


@router.post("/query", response_model=QueryResponse)
async def execute_query(query_request: QueryRequest, current_user_id: str = Depends(security_service.get_current_user_id)):
    """Выполнить SQL запрос"""
    try:
        if not query_request.sql:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SQL query is required")
        
        # Простая проверка безопасности - разрешаем только SELECT запросы
        sql_upper = query_request.sql.strip().upper()
        if not sql_upper.startswith('SELECT'):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only SELECT queries are allowed")
        
        start_time = time.time()
        
        async with app_database_service.pool.acquire() as conn:
            rows = await conn.fetch(query_request.sql)
            
        execution_time = time.time() - start_time
        
        # Преобразуем результат в список словарей
        data = [dict(row) for row in rows]
        
        # Сохраняем в историю запросов
        try:
            await app_database_service.save_query_history(
                user_id=current_user_id,
                natural_query=query_request.natural_query or "",
                sql_query=query_request.sql,
                explanation=query_request.explanation,
                execution_time=execution_time
            )
        except Exception as e:
            logger.warning(f"Failed to save query history: {e}")
        
        return QueryResponse(
            data=data,
            sql=query_request.sql,
            explanation=query_request.explanation,
            row_count=len(data),
            execution_time=execution_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        # Специальная обработка для ошибки с demo1.ddd
        error_msg = str(e)
        if "demo1.ddd" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Таблица 'demo1.ddd' не существует. Проверьте правильность имени таблицы и схемы."
            )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Query execution failed: {error_msg}")


@router.get("/sample-data/{table_name}")
async def get_sample_data(
    table_name: str, 
    limit: int = 10, 
    current_user_id: str = Depends(security_service.get_current_user_id)
):
    """Получить примеры данных из таблицы"""
    try:
        # Проверяем что таблица существует
        async with app_database_service.pool.acquire() as conn:
            table_exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = $1
                )
            """, table_name)
            
            if not table_exists:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table not found")
            
            # Получаем примеры данных
            query = f"SELECT * FROM {table_name} LIMIT {min(limit, 100)}"
            rows = await conn.fetch(query)
            
            # Получаем информацию о колонках
            columns = await conn.fetch("""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_name = $1 
                AND table_schema = 'public'
                ORDER BY ordinal_position
            """, table_name)
            
            column_info = [{"name": col['column_name'], "type": col['data_type']} for col in columns]
            data = [dict(row) for row in rows]
            
            return {
                "table_name": table_name,
                "columns": column_info,
                "data": data,
                "total_rows": len(data)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sample data for table {table_name}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get sample data")


@router.get("/schema", response_model=DatabaseSchema)
async def get_database_schema(current_user_id: str = Depends(security_service.get_current_user_id)):
    """Получить схему базы данных"""
    try:
        tables = await get_tables(current_user_id)
        table_columns = {}
        
        for table in tables:
            columns = await get_table_columns(table.name, current_user_id)
            table_columns[table.name] = columns
            
        return DatabaseSchema(tables=tables, table_columns=table_columns)
        
    except Exception as e:
        logger.error(f"Error getting database schema: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get database schema")
