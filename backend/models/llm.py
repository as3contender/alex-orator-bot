from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class SQLGenerationRequest(BaseModel):
    """Запрос на генерацию SQL"""

    user_query: str = Field(..., description="Запрос пользователя на естественном языке")
    tables_info: List[Dict[str, Any]] = Field(..., description="Информация о таблицах")
    user_language: str = Field(default="ru", description="Язык пользователя")


class SQLGenerationResponse(BaseModel):
    """Ответ с сгенерированным SQL"""

    sql: str = Field(..., description="Сгенерированный SQL запрос")
    explanation: str = Field(..., description="Объяснение запроса")
    confidence: float = Field(..., ge=0, le=1, description="Уверенность в правильности")
    suggested_improvements: Optional[List[str]] = Field(None, description="Предложения по улучшению")


class LLMConfig(BaseModel):
    """Конфигурация LLM"""

    model: str = Field(default="gpt-3.5-turbo", description="Модель OpenAI")
    max_tokens: int = Field(default=1000, ge=1, le=4000, description="Максимальное количество токенов")
    temperature: float = Field(default=0.1, ge=0, le=2, description="Температура генерации")
    system_prompt: str = Field(..., description="Системный промпт для LLM")
