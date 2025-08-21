from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from datetime import datetime

from models.orator import MatchRequest, MatchResponse
from services.security import security_service
from services.matching_service import matching_service

router = APIRouter()


@router.post("/find", response_model=MatchResponse)
async def find_candidates(
    match_request: MatchRequest, current_user_id: str = Depends(security_service.get_current_user_id)
):
    """Найти кандидатов для пары"""
    try:
        # Преобразуем строку даты в объект date
        week_start_date = datetime.strptime(match_request.week_start_date, "%Y-%m-%d").date()

        candidates = await matching_service.find_candidates(
            user_id=current_user_id, week_start=week_start_date, limit=match_request.limit
        )
        return MatchResponse(candidates=candidates)
    except Exception as e:
        logger.error(f"Find candidates error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to find candidates")
