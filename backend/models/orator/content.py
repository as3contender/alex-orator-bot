from pydantic import BaseModel, Field
from typing import Optional

from .base import BaseEntity


class BotContent(BaseEntity):
    """Контент бота (тексты, сообщения)"""

    content_key: str = Field(..., description="Ключ контента, например: 'welcome_message'")
    content_text: str = Field(..., description="Текст с поддержкой markdown")
    language: str = Field(default="ru", description="Язык контента")
    is_active: bool = True


class BotContentCreate(BaseModel):
    """Создание контента"""

    content_key: str
    content_text: str
    language: str = "ru"


class BotContentUpdate(BaseModel):
    """Обновление контента"""

    content_text: Optional[str] = None
    is_active: Optional[bool] = None
