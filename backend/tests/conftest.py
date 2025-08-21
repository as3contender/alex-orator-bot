import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """Синхронный тестовый клиент"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Асинхронный тестовый клиент"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# Убираем фикстуру test_db для упрощения


@pytest.fixture
def sample_telegram_user():
    """Образец данных Telegram пользователя"""
    return {"telegram_id": "123456789", "telegram_username": "test_user", "first_name": "Test", "last_name": "User"}


@pytest.fixture
def sample_user_data():
    """Образец данных пользователя для регистрации"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123",
        "first_name": "Test",
        "last_name": "User",
    }
