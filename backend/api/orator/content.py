from fastapi import APIRouter, HTTPException, status
from loguru import logger

from models.orator import BotContent
from services.orator_database import orator_db

router = APIRouter()


@router.get("/{content_key}", response_model=BotContent)
async def get_bot_content(content_key: str):
    """Получить контент бота по ключу"""
    try:
        content = await orator_db.get_bot_content(content_key)
        if not content:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
        return content
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get bot content error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get content")
