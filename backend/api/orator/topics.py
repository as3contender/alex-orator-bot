from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from typing import List

from models.orator import TopicTree, UserTopic
from services.security import security_service
from services.orator_database import orator_db

router = APIRouter()


@router.get("/tree", response_model=TopicTree)
async def get_topic_tree():
    """Получить дерево тем"""
    try:
        topic_tree = await orator_db.get_topic_tree()
        return topic_tree
    except Exception as e:
        logger.error(f"Get topic tree error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get topic tree")


@router.get("/user", response_model=List[UserTopic])
async def get_user_topics(current_user_id: str = Depends(security_service.get_current_user_id)):
    """Получить темы пользователя для текущей недели"""
    try:
        # Получаем текущую регистрацию
        registration = await orator_db.get_user_week_registration(current_user_id)
        if not registration:
            return []

        topics = await orator_db.get_user_topics(registration["id"])
        return topics
    except Exception as e:
        logger.error(f"Get user topics error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user topics")
