from pydantic import BaseModel
from typing import List, Optional

from .enums import Gender


class CandidateInfo(BaseModel):
    """Информация о кандидате для подбора пары"""

    user_id: str
    name: str
    gender: Optional[Gender] = None
    total_sessions: int
    preferred_time_msk: str
    selected_topics: List[str]
    match_score: float = 0.0


class MatchRequest(BaseModel):
    """Запрос на подбор пары"""

    week_start_date: str
    limit: int = 3


class MatchResponse(BaseModel):
    """Ответ с кандидатами для подбора"""

    candidates: List[CandidateInfo]
