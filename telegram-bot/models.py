from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class TelegramUser(BaseModel):
    """Модель пользователя Telegram"""

    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None


class QueryRequest(BaseModel):
    """Модель запроса пользователя"""

    user_id: int
    chat_id: int
    message_id: int
    text: str
    language: str = "ru"


class QueryResponse(BaseModel):
    """Модель ответа на запрос"""

    success: bool
    message: str
    data: Optional[List[Dict[str, Any]]] = None
    sql: Optional[str] = None
    explanation: Optional[str] = None
    error: Optional[str] = None


class UserSettings(BaseModel):
    """Модель настроек пользователя"""

    language: str = "ru"
    show_explanations: bool = True
    show_sql: bool = True
    max_results: int = 100
    auto_format: bool = True


class TableInfo(BaseModel):
    """Модель информации о таблице"""

    name: str
    description: Optional[str] = None
    row_count: Optional[int] = None


class SampleData(BaseModel):
    """Модель примера данных"""

    table: str
    data: List[Dict[str, Any]]
