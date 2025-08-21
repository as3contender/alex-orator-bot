from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class TableInfo(BaseModel):
    """Информация о таблице"""

    name: str
    description: Optional[str] = None
    row_count: Optional[int] = None


class ColumnInfo(BaseModel):
    """Информация о колонке"""

    name: str
    data_type: str
    is_nullable: bool
    description: Optional[str] = None


class QueryRequest(BaseModel):
    """Запрос на выполнение SQL"""

    sql: Optional[str] = None
    natural_query: Optional[str] = None
    explanation: Optional[str] = None


class QueryResponse(BaseModel):
    """Ответ с результатами запроса"""

    data: List[Dict[str, Any]]
    sql: str
    explanation: Optional[str] = None
    row_count: int
    execution_time: Optional[float] = None


class DatabaseSchema(BaseModel):
    """Схема базы данных"""

    tables: List[TableInfo]
    table_columns: Dict[str, List[ColumnInfo]]


class SampleDataRequest(BaseModel):
    """Запрос на получение примера данных"""

    table_name: str
    limit: int = Field(default=10, ge=1, le=100)
