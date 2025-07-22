from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

from .base import BaseEntity
from .enums import Gender


class UserProfile(BaseModel):
    """Расширенный профиль пользователя"""

    telegram_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[Gender] = None
    registration_date: datetime
    total_sessions: int = 0
    feedback_count: int = 0
    is_active: bool = True


class UserProfileUpdate(BaseModel):
    """Обновление профиля пользователя"""

    gender: Optional[Gender] = None
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)


class UserStats(BaseModel):
    """Статистика пользователя"""

    total_sessions: int
    feedback_given: int
    feedback_received: int
    average_rating: float
    registration_count: int
    can_register_again: bool


class User(BaseEntity):
    """Модель пользователя Alex Orator Bot"""

    telegram_id: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[Gender] = None
    registration_date: datetime
    total_sessions: int = 0
    feedback_count: int = 0
    is_active: bool = True


class UserResponse(BaseModel):
    """Модель ответа с информацией о пользователе Alex Orator Bot"""

    id: UUID
    telegram_id: str
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    gender: Optional[Gender]
    registration_date: datetime
    total_sessions: int
    feedback_count: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    @classmethod
    def from_user(cls, user: User):
        """Создание ответа из объекта пользователя"""
        return cls(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            gender=user.gender,
            registration_date=user.registration_date,
            total_sessions=user.total_sessions,
            feedback_count=user.feedback_count,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


class TokenResponse(BaseModel):
    """Модель ответа с токеном для Alex Orator Bot"""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
