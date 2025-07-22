from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

from .base import BaseEntity
from .enums import WeekType, RegistrationStatus


class WeekRegistration(BaseEntity):
    """Регистрация пользователя на неделю"""

    user_id: str
    week_start_date: date
    week_end_date: date
    preferred_time_msk: str = Field(..., description="Время в формате HH:MM по МСК")
    status: RegistrationStatus = RegistrationStatus.ACTIVE
    cancelled_at: Optional[datetime] = None


class WeekRegistrationCreate(BaseModel):
    """Создание регистрации на неделю"""

    week_type: WeekType
    preferred_time_msk: str = Field(..., description="Время в формате HH:MM по МСК")
    selected_topics: List[str] = Field(default=[], description="Список выбранных тем")


class WeekRegistrationUpdate(BaseModel):
    """Обновление регистрации на неделю"""

    preferred_time_msk: Optional[str] = Field(None, description="Время в формате HH:MM по МСК")
    selected_topics: Optional[List[str]] = Field(None, description="Список выбранных тем")


class WeekRegistrationResponse(BaseModel):
    """Ответ с информацией о регистрации"""

    id: str
    week_start_date: date
    week_end_date: date
    preferred_time_msk: str
    status: RegistrationStatus
    created_at: datetime
    cancelled_at: Optional[datetime] = None
    selected_topics: List[str] = Field(default=[], description="Список выбранных тем")


class WeekInfo(BaseModel):
    """Информация о неделе"""

    week_start_date: date
    week_end_date: date
    is_current: bool
    registration_deadline: datetime
