from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


class BaseResponse(BaseModel):
    """Базовая модель ответа"""

    success: bool = True
    message: Optional[str] = None


class BaseEntity(BaseModel):
    """Базовая модель сущности"""

    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class PaginationParams(BaseModel):
    """Параметры пагинации"""

    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Ответ с пагинацией"""

    items: list
    total: int
    page: int
    size: int
    pages: int
