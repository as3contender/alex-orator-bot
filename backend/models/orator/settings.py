from pydantic import BaseModel, Field
from typing import Optional

from .base import BaseEntity


class OratorSettings(BaseEntity):
    """Настройки ораторского бота"""

    key: str = Field(..., description="Ключ настройки")
    value: str = Field(..., description="Значение настройки")
    description: Optional[str] = Field(None, description="Описание настройки")
    is_active: bool = True


class OratorSettingsUpdate(BaseModel):
    """Обновление настроек"""

    value: str
    description: Optional[str] = None
    is_active: Optional[bool] = None


# Предопределенные ключи настроек
class OratorSettingKeys:
    """Ключи настроек ораторского бота"""

    MAX_PAIRS_PER_USER = "max_pairs_per_user"
    MAX_CANDIDATES_PER_REQUEST = "max_candidates_per_request"
    REGISTRATION_DEADLINE_HOURS = "registration_deadline_hours"
    FEEDBACK_REQUIRED_FOR_REREGISTRATION = "feedback_required_for_reregistration"
    MIN_FEEDBACK_LENGTH = "min_feedback_length"
    MAX_FEEDBACK_LENGTH = "max_feedback_length"
    SESSION_DURATION_MINUTES = "session_duration_minutes"
    AUTO_CANCEL_PENDING_PAIRS_HOURS = "auto_cancel_pending_pairs_hours"
