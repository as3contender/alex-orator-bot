from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from typing import List

from models.orator import SessionFeedbackCreate, SessionFeedbackResponse
from services.security import security_service
from services.orator_database import orator_db

router = APIRouter()


@router.post("/", response_model=SessionFeedbackResponse)
async def create_feedback(
    feedback_data: SessionFeedbackCreate, current_user_id: str = Depends(security_service.get_current_user_id)
):
    """Создать обратную связь"""
    try:
        feedback = await orator_db.create_session_feedback(
            pair_id=feedback_data.pair_id,
            from_user_id=current_user_id,
            feedback_text=feedback_data.feedback_text,
            rating=feedback_data.rating,
        )

        if not feedback:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create feedback")

        return SessionFeedbackResponse.from_session_feedback(feedback)
    except Exception as e:
        logger.error(f"Create feedback error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create feedback")


@router.get("/received", response_model=List[SessionFeedbackResponse])
async def get_received_feedback(current_user_id: str = Depends(security_service.get_current_user_id)):
    """Получить полученную обратную связь"""
    try:
        feedback_list = await orator_db.get_session_feedback_by_user(to_user_id=current_user_id)
        return [SessionFeedbackResponse.from_session_feedback(f) for f in feedback_list]
    except Exception as e:
        logger.error(f"Get received feedback error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get feedback")


@router.get("/given", response_model=List[SessionFeedbackResponse])
async def get_given_feedback(current_user_id: str = Depends(security_service.get_current_user_id)):
    """Получить данную обратную связь"""
    try:
        feedback_list = await orator_db.get_session_feedback_by_user(from_user_id=current_user_id)
        return [SessionFeedbackResponse.from_session_feedback(f) for f in feedback_list]
    except Exception as e:
        logger.error(f"Get given feedback error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get feedback")
