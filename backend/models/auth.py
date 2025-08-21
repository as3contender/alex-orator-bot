from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

from .base import BaseEntity


class UserLogin(BaseModel):
    """Модель для входа пользователя"""

    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6)


class UserCreate(BaseModel):
    """Модель для создания пользователя"""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)


class UserResponse(BaseModel):
    """Модель ответа с информацией о пользователе"""

    id: UUID
    email: str
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    telegram_id: Optional[str]
    telegram_username: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    @classmethod
    def from_user(cls, user):
        """Создание ответа из объекта пользователя"""
        return cls(
            id=user.id,
            email=user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            telegram_id=user.telegram_id,
            telegram_username=user.telegram_username,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


class TokenResponse(BaseModel):
    """Модель ответа с токеном"""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class User(BaseEntity):
    """Модель пользователя в базе данных"""

    email: str
    username: str
    hashed_password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    telegram_id: Optional[str] = None
    telegram_username: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
