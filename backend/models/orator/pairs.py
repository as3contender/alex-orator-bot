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
    partner_username: str
    partner_telegram_id: str
    partner_name: str
    week_start_date: date
    week_end_date: date
    status: PairStatus
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    has_feedback: bool = False
    is_initiator: bool = False

    @classmethod
    def from_user_pair(cls, user_pair: dict) -> "UserPairResponse":
        """Создать ответ из данных пары пользователей"""
        return cls(
            id=str(user_pair["id"]),
            partner_id=str(user_pair["partner_id"]),
            partner_username=user_pair["partner_username"],
            partner_telegram_id=user_pair["partner_telegram_id"],
            partner_name=user_pair["partner_name"],
            week_start_date=user_pair["week_start_date"],
            week_end_date=user_pair["week_end_date"],
            status=user_pair["status"],
            created_at=user_pair["created_at"],
            confirmed_at=user_pair.get("confirmed_at"),
            cancelled_at=user_pair.get("cancelled_at"),
            has_feedback=user_pair.get("has_feedback", False),
            is_initiator=user_pair.get("is_initiator", False),
        )


class PairConfirmation(BaseModel):
    """Подтверждение пары"""

    pair_id: str
    confirmed: bool
