"""
API эндпоинты для контента бота
"""

from fastapi import APIRouter, HTTPException, Depends
from loguru import logger

from services.orator_database import orator_db

router = APIRouter(prefix="/content", tags=["content"])


@router.get("/test")
async def test_content_endpoint():
    """Тестовый эндпоинт для проверки работы роутера"""
    logger.info("test_content_endpoint called")
    return {"message": "Content router is working!"}


@router.get("/exercise/{topic_id}")
async def get_exercise_by_topic(
    topic_id: str,
    language: str = "ru",
):
    """
    Получить упражнения по теме (дочерние элементы)

    Args:
        topic_id: ID темы (например, 'речевая_импровизация_уровень_1')
        language: Язык контента (по умолчанию 'ru')

    Returns:
        Массив упражнений для указанной темы
    """
    try:
        logger.info(f"get_exercise_by_topic called with topic_id: '{topic_id}', language: '{language}'")

        # Получаем все упражнения, которые начинаются с указанного topic_id
        exercises = await orator_db.get_exercises_by_topic(topic_id, language)

        logger.info(
            f"get_exercise_by_topic: orator_db.get_exercises_by_topic returned {len(exercises) if exercises else 0} exercises"
        )

        if not exercises:
            logger.warning(f"No exercises found for topic_id: '{topic_id}', language: '{language}'")
            raise HTTPException(
                status_code=404, detail=f"Exercises for topic '{topic_id}' and language '{language}' not found"
            )

        logger.info(f"get_exercise_by_topic: returning {len(exercises)} exercises for topic_id: '{topic_id}'")
        return {"topic_id": topic_id, "exercises": exercises, "language": language, "count": len(exercises)}

    except HTTPException:
        # Пробрасываем HTTPException как есть
        raise
    except Exception as e:
        logger.error(f"Error getting exercises by topic: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/messages/{message_key}")
async def get_bot_message(
    message_key: str,
    language: str = "ru",
):
    """
    Получить сообщение бота по ключу

    Args:
        message_key: Ключ сообщения (например, 'приветственное_сообщение')
        language: Язык контента (по умолчанию 'ru')

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


@router.get("/{content_key}")
async def get_bot_content(
    content_key: str,
    language: str = "ru",
):
    """
    Получить контент бота по ключу

    Args:
        content_key: Ключ контента (например, 'приветственное_сообщение')
        language: Язык контента (по умолчанию 'ru')

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
