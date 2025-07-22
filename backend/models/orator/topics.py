from pydantic import BaseModel, Field
from typing import Optional, List

from .base import BaseEntity


class TopicNode(BaseModel):
    """Узел дерева тем"""

    id: str
    name: str
    description: Optional[str] = None
    children: Optional[List["TopicNode"]] = None


class UserTopic(BaseEntity):
    """Выбранная тема пользователя"""

    user_id: str
    week_registration_id: str
    topic_path: str = Field(..., description="Путь к теме, например: 'Подача - Темы речи уровень 1'")


class UserTopicCreate(BaseModel):
    """Создание выбранной темы"""

    topic_path: str


class TopicTree(BaseModel):
    """Дерево тем"""

    topics: List[TopicNode]
    language: str = "ru"
