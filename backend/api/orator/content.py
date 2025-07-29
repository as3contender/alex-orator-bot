"""
API эндпоинты для контента бота
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from loguru import logger

from services.orator_database import OratorDatabaseService
from services.auth_service import get_current_user
from models.orator import User

router = APIRouter(prefix="/content", tags=["content"])


@router.get("/{content_key}")
async def get_bot_content(
    content_key: str,
    language: str = "ru",
    current_user: User = Depends(get_current_user),
    orator_db: OratorDatabaseService = Depends(),
):
    """
    Получить контент бота по ключу

    Args:
        content_key: Ключ контента (например, 'приветственное_сообщение')
        language: Язык контента (по умолчанию 'ru')
        current_user: Текущий пользователь
        orator_db: Сервис базы данных

    Returns:
        Контент бота
    """
    try:
        content = await orator_db.get_bot_content(content_key, language)

        if not content:
            raise HTTPException(
                status_code=404, detail=f"Content with key '{content_key}' and language '{language}' not found"
            )

        return {"content_key": content_key, "content_text": content, "language": language}

    except Exception as e:
        logger.error(f"Error getting bot content: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/exercise/{topic_id}")
async def get_exercise_by_topic(
    topic_id: str,
    language: str = "ru",
    current_user: User = Depends(get_current_user),
    orator_db: OratorDatabaseService = Depends(),
):
    """
    Получить упражнение по теме

    Args:
        topic_id: ID темы (например, 'речевая_импровизация_уровень_1_задание_1')
        language: Язык контента (по умолчанию 'ru')
        current_user: Текущий пользователь
        orator_db: Сервис базы данных

    Returns:
        Упражнение для указанной темы
    """
    try:
        # Формируем ключ упражнения
        exercise_key = f"exercise_{topic_id}"

        content = await orator_db.get_bot_content(exercise_key, language)

        if not content:
            raise HTTPException(
                status_code=404, detail=f"Exercise for topic '{topic_id}' and language '{language}' not found"
            )

        return {"topic_id": topic_id, "exercise_key": exercise_key, "content_text": content, "language": language}

    except Exception as e:
        logger.error(f"Error getting exercise by topic: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/messages/{message_key}")
async def get_bot_message(
    message_key: str,
    language: str = "ru",
    current_user: User = Depends(get_current_user),
    orator_db: OratorDatabaseService = Depends(),
):
    """
    Получить сообщение бота по ключу

    Args:
        message_key: Ключ сообщения (например, 'приветственное_сообщение')
        language: Язык контента (по умолчанию 'ru')
        current_user: Текущий пользователь
        orator_db: Сервис базы данных

    Returns:
        Сообщение бота
    """
    try:
        content = await orator_db.get_bot_content(message_key, language)

        if not content:
            raise HTTPException(
                status_code=404, detail=f"Message with key '{message_key}' and language '{language}' not found"
            )

        return {"message_key": message_key, "content_text": content, "language": language}

    except Exception as e:
        logger.error(f"Error getting bot message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
