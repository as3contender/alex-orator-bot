from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid


class MessageQueue(BaseModel):
    """Очередь сообщений"""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    message: str
    sent: bool = False
    created_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
