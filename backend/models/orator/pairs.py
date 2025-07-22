from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

from .base import BaseEntity
from .enums import PairStatus


class UserPair(BaseEntity):
    """Пара пользователей"""

    user1_id: str
    user2_id: str
    week_registration_id: str
    status: PairStatus = PairStatus.PENDING
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None


class UserPairResponse(BaseModel):
    """Ответ с информацией о паре"""

    id: str
    partner_id: str
    partner_name: str
    week_start_date: date
    week_end_date: date
    status: PairStatus
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    has_feedback: bool = False


class PairConfirmation(BaseModel):
    """Подтверждение пары"""

    pair_id: str
    confirmed: bool
