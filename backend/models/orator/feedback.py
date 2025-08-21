from pydantic import BaseModel, Field
from datetime import datetime

from .base import BaseEntity
from .enums import FeedbackRating


class SessionFeedback(BaseEntity):
    """Обратная связь по занятию"""

    pair_id: str
    from_user_id: str
    feedback_text: str = Field(..., min_length=3, max_length=1000)
    rating: FeedbackRating


class SessionFeedbackCreate(BaseModel):
    """Создание обратной связи"""

    pair_id: str
    feedback_text: str = Field(..., min_length=3, max_length=1000)
    rating: FeedbackRating


class SessionFeedbackResponse(BaseModel):
    """Ответ с обратной связью"""

    id: str
    from_user_name: str
    feedback_text: str
    rating: FeedbackRating
    created_at: datetime

    @classmethod
    def from_session_feedback(cls, feedback: dict) -> "SessionFeedbackResponse":
        """Создать ответ из данных обратной связи"""
        return cls(
            id=str(feedback["id"]),
            from_user_name=feedback.get("from_user_name", "Пользователь"),
            feedback_text=feedback["feedback_text"],
            rating=feedback["rating"],
            created_at=feedback["created_at"],
        )
