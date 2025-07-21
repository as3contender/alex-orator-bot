from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

from .base import BaseEntity


class UserSettings(BaseEntity):
    """Настройки пользователя"""

    user_id: UUID
    language: str = Field(default="ru", description="Язык интерфейса (ru/en)")
    show_explanations: bool = Field(default=True, description="Показывать объяснения SQL")
    show_sql: bool = Field(default=True, description="Показывать SQL запросы")
    max_results: int = Field(default=100, ge=1, le=1000, description="Максимальное количество результатов")
    auto_format: bool = Field(default=True, description="Автоматическое форматирование результатов")


class UserSettingsUpdate(BaseModel):
    """Модель для обновления настроек"""

    language: Optional[str] = Field(None, description="Язык интерфейса (ru/en)")
    show_explanations: Optional[bool] = Field(None, description="Показывать объяснения SQL")
    show_sql: Optional[bool] = Field(None, description="Показывать SQL запросы")
    max_results: Optional[int] = Field(None, ge=1, le=1000, description="Максимальное количество результатов")
    auto_format: Optional[bool] = Field(None, description="Автоматическое форматирование результатов")
