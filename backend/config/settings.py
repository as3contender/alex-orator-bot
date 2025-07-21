from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Основные настройки
    debug: bool = False
    secret_key: str = "your-secret-key-change-in-production"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    openai_max_tokens: int = 1000
    openai_temperature: float = 0.1

    # Базы данных
    app_database_url: str = "postgresql://user:pass@localhost:5432/app_db"
    data_database_url: str = "postgresql://user:pass@localhost:5433/data_db"

    # JWT
    jwt_secret_key: str = "your-jwt-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # CORS
    cors_origins: List[str] = ["*"]

    # Логирование
    log_level: str = "INFO"
    log_file: str = "logs/backend.log"

    # API
    api_prefix: str = "/api/v1"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Создание экземпляра настроек
settings = Settings()

# Создание директории для логов
os.makedirs("logs", exist_ok=True)
