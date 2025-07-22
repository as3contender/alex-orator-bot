import pytest
from httpx import AsyncClient
from fastapi import status

from models.telegram import TelegramAuth


class TestAuthAPI:
    """Тесты для API аутентификации"""

    @pytest.mark.asyncio
    async def test_health_check(self, async_client: AsyncClient):
        """Тест проверки здоровья API"""
        response = await async_client.get("/api/v1/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_telegram_auth_success(self, async_client: AsyncClient, sample_telegram_user):
        """Тест успешной аутентификации через Telegram"""
        telegram_data = TelegramAuth(**sample_telegram_user)

        response = await async_client.post("/api/v1/auth/telegram", json=telegram_data.model_dump())

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Проверяем структуру ответа
        assert "access_token" in data
        assert "token_type" in data
        assert "user" in data
        assert data["token_type"] == "bearer"

        # Проверяем данные пользователя
        user = data["user"]
        assert user["telegram_id"] == sample_telegram_user["telegram_id"]
        assert user["username"] == sample_telegram_user["telegram_username"]
        assert user["first_name"] == sample_telegram_user["first_name"]
        assert user["last_name"] == sample_telegram_user["last_name"]
        assert "id" in user
        assert "registration_date" in user
        assert "total_sessions" in user
        assert "feedback_count" in user
        assert "is_active" in user

    @pytest.mark.asyncio
    async def test_telegram_auth_invalid_data(self, async_client: AsyncClient):
        """Тест аутентификации с некорректными данными"""
        invalid_data = {
            "telegram_id": "",  # Пустой telegram_id
            "telegram_username": "test_user",
            "first_name": "Test",
            "last_name": "User",
        }

        response = await async_client.post("/api/v1/auth/telegram", json=invalid_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_telegram_auth_missing_required_field(self, async_client: AsyncClient):
        """Тест аутентификации без обязательного поля"""
        incomplete_data = {
            "telegram_username": "test_user",
            "first_name": "Test",
            "last_name": "User",
            # Отсутствует telegram_id
        }

        response = await async_client.post("/api/v1/auth/telegram", json=incomplete_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_telegram_auth_duplicate_user(self, async_client: AsyncClient, sample_telegram_user):
        """Тест повторной аутентификации того же пользователя"""
        telegram_data = TelegramAuth(**sample_telegram_user)

        # Первая аутентификация
        response1 = await async_client.post("/api/v1/auth/telegram", json=telegram_data.model_dump())
        assert response1.status_code == status.HTTP_200_OK

        # Вторая аутентификация того же пользователя
        response2 = await async_client.post("/api/v1/auth/telegram", json=telegram_data.model_dump())
        assert response2.status_code == status.HTTP_200_OK

        # Проверяем, что пользователь тот же
        user1 = response1.json()["user"]
        user2 = response2.json()["user"]
        assert user1["id"] == user2["id"]
        assert user1["telegram_id"] == user2["telegram_id"]

    @pytest.mark.asyncio
    async def test_get_current_user_with_token(self, async_client: AsyncClient, sample_telegram_user):
        """Тест получения информации о текущем пользователе с токеном"""
        # Сначала аутентифицируемся
        telegram_data = TelegramAuth(**sample_telegram_user)
        auth_response = await async_client.post("/api/v1/auth/telegram", json=telegram_data.model_dump())
        assert auth_response.status_code == status.HTTP_200_OK

        token = auth_response.json()["access_token"]

        # Получаем информацию о пользователе
        headers = {"Authorization": f"Bearer {token}"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)

        assert response.status_code == status.HTTP_200_OK
        user_data = response.json()
        assert user_data["telegram_id"] == sample_telegram_user["telegram_id"]

    @pytest.mark.asyncio
    async def test_get_current_user_without_token(self, async_client: AsyncClient):
        """Тест получения информации о пользователе без токена"""
        response = await async_client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, async_client: AsyncClient):
        """Тест получения информации о пользователе с неверным токеном"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await async_client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
