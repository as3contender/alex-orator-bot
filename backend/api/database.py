from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from typing import List, Dict, Any

from models.database import TableInfo, ColumnInfo, QueryRequest, QueryResponse
from services.data_database import data_database_service
from services.llm_service import llm_service
from services.security import security_service

router = APIRouter()


@router.get("/tables", response_model=List[TableInfo])
async def get_tables(current_user_id: str = Depends(security_service.get_current_user_id)):
    """Получение списка доступных таблиц"""
    try:
        tables = await data_database_service.get_tables()
        logger.info(f"User {current_user_id} requested tables list")
        return tables
    except Exception as e:
        logger.error(f"Get tables error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get tables")


@router.get("/tables/{table_name}/columns", response_model=List[ColumnInfo])
async def get_table_columns(table_name: str, current_user_id: str = Depends(security_service.get_current_user_id)):
    """Получение информации о колонках таблицы"""
    try:
        columns = await data_database_service.get_table_columns(table_name)
        logger.info(f"User {current_user_id} requested columns for table {table_name}")
        return columns
    except Exception as e:
        logger.error(f"Get columns error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get columns")


@router.post("/query", response_model=QueryResponse)
async def execute_query(
    query_request: QueryRequest, current_user_id: str = Depends(security_service.get_current_user_id)
):
    """Выполнение SQL запроса (только SELECT)"""
    try:
        # Валидация SQL запроса
        if not query_request.sql.strip().upper().startswith("SELECT"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only SELECT queries are allowed")

        # Выполнение запроса
        result = await data_database_service.execute_query(query_request.sql)
        logger.info(f"User {current_user_id} executed query: {query_request.sql[:100]}...")

        return QueryResponse(data=result, sql=query_request.sql, explanation=query_request.explanation)
    except Exception as e:
        logger.error(f"Query execution error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Query execution failed")


@router.post("/natural-query", response_model=QueryResponse)
async def natural_language_query(
    query_request: QueryRequest, current_user_id: str = Depends(security_service.get_current_user_id)
):
    """Обработка запроса на естественном языке"""
    try:
        # Получение схемы базы данных
        tables_info = await data_database_service.get_database_schema()

        # Генерация SQL через LLM
        sql_result = await llm_service.generate_sql_query(
            user_query=query_request.natural_query,
            tables_info=tables_info,
            user_language="ru",  # TODO: получить из настроек пользователя
        )

        # Выполнение сгенерированного SQL
        result = await data_database_service.execute_query(sql_result.sql)

        logger.info(f"User {current_user_id} made natural query: {query_request.natural_query}")

        return QueryResponse(data=result, sql=sql_result.sql, explanation=sql_result.explanation)
    except Exception as e:
        logger.error(f"Natural query error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Natural language query failed")


@router.get("/sample-data/{table_name}")
async def get_sample_data(
    table_name: str, limit: int = 10, current_user_id: str = Depends(security_service.get_current_user_id)
):
    """Получение примера данных из таблицы"""
    try:
        sample_data = await data_database_service.get_sample_data(table_name, limit)
        logger.info(f"User {current_user_id} requested sample data from {table_name}")
        return {"table": table_name, "data": sample_data}
    except Exception as e:
        logger.error(f"Get sample data error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get sample data")
