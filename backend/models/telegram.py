from pydantic import BaseModel, Field
from typing import Optional


class TelegramAuth(BaseModel):
    """Модель для аутентификации через Telegram"""

    telegram_id: str = Field(..., min_length=1, description="Telegram ID пользователя")
    telegram_username: Optional[str] = Field(None, description="Telegram username")
    first_name: Optional[str] = Field(None, description="Имя пользователя")
    last_name: Optional[str] = Field(None, description="Фамилия пользователя")


class TelegramMessage(BaseModel):
    """Модель сообщения от Telegram"""

    message_id: int
    chat_id: int
    user_id: int
    text: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class TelegramResponse(BaseModel):
    """Модель ответа для Telegram"""

    chat_id: int
    text: str
    parse_mode: Optional[str] = "HTML"
    reply_markup: Optional[dict] = None
