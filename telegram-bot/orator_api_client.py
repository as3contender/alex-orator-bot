import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from datetime import date, datetime
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from config import API_TIMEOUT, API_RETRY_ATTEMPTS, API_RETRY_DELAY
from exceptions import BackendConnectionError, AuthenticationError


class OratorAPIClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None
        self.auth_token: Optional[str] = None

    async def __aenter__(self):
        """Асинхронный контекстный менеджер - вход"""
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=API_TIMEOUT))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Асинхронный контекстный менеджер - выход"""
        if self.session:
            await self.session.close()

    async def check_connection(self):
        """Проверка подключения к backend"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/v1/health") as response:
                    if response.status == 200:
                        logger.info("Backend connection successful")
                        return True
                    else:
                        raise BackendConnectionError(f"Backend health check failed: {response.status}")
        except Exception as e:
            logger.error(f"Backend connection check failed: {e}")
            raise BackendConnectionError(f"Failed to connect to backend: {e}")

    async def _make_request_without_retry(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Выполнить HTTP запрос без retry логики"""
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.get("headers", {})
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        kwargs["headers"] = headers

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, **kwargs) as response:
                    if response.status == 401:
                        raise AuthenticationError("Authentication required")
                    elif response.status >= 400:
                        error_text = await response.text()
                        logger.error(f"API request failed: {response.status} - {error_text}")
                        raise BackendConnectionError(f"API request failed: {response.status}")

                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request failed: {e}")
            raise BackendConnectionError(f"HTTP request failed: {e}")

    @retry(
        stop=stop_after_attempt(API_RETRY_ATTEMPTS), wait=wait_exponential(multiplier=1, min=API_RETRY_DELAY, max=10)
    )
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Выполнение HTTP запроса с retry логикой"""
        url = f"{self.base_url}{endpoint}"

        # Добавляем заголовки авторизации
        headers = kwargs.get("headers", {})
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        kwargs["headers"] = headers

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, **kwargs) as response:
                    if response.status == 401:
                        raise AuthenticationError("Authentication required")
                    elif response.status >= 400:
                        error_text = await response.text()
                        logger.error(f"API request failed: {response.status} - {error_text}")
                        raise BackendConnectionError(f"API request failed: {response.status}")

                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request failed: {e}")
            raise BackendConnectionError(f"HTTP request failed: {e}")

    async def authenticate_telegram_user(
        self, telegram_id: str, username: str = None, first_name: str = None, last_name: str = None
    ) -> str:
        """Аутентификация пользователя через Telegram"""
        data = {
            "telegram_id": telegram_id,
            "telegram_username": username,
            "first_name": first_name,
            "last_name": last_name,
        }

        response = await self._make_request("POST", "/api/v1/auth/telegram", json=data)
        self.auth_token = response["access_token"]
        return self.auth_token

    # ============================================================================
    # ПРОФИЛИ ПОЛЬЗОВАТЕЛЕЙ
    # ============================================================================

    async def get_user_profile(self) -> Dict[str, Any]:
        """Получить профиль пользователя"""
        return await self._make_request("GET", "/api/v1/orator/profile")

    async def update_user_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обновить профиль пользователя"""
        return await self._make_request("PUT", "/api/v1/orator/profile", json=profile_data)

    async def get_user_stats(self) -> Dict[str, Any]:
        """Получить статистику пользователя"""
        return await self._make_request("GET", "/api/v1/orator/stats")

    # ============================================================================
    # РЕГИСТРАЦИИ НА НЕДЕЛИ
    # ============================================================================

    async def get_week_info(self) -> Dict[str, Any]:
        """Получить информацию о текущей неделе"""
        return await self._make_request("GET", "/api/v1/orator/weeks/info")

    async def get_current_registration(self) -> Optional[Dict[str, Any]]:
        """Получить текущую регистрацию пользователя"""
        return await self._make_request("GET", "/api/v1/orator/weeks/current")

    async def register_for_week(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Зарегистрироваться на неделю"""
        return await self._make_request("POST", "/api/v1/orator/weeks/register", json=registration_data)

    async def cancel_registration(self) -> Dict[str, str]:
        """Отменить регистрацию на неделю"""
        return await self._make_request("DELETE", "/api/v1/orator/weeks/cancel")

    # ============================================================================
    # ТЕМЫ
    # ============================================================================

    async def get_topic_tree(self) -> Dict[str, Any]:
        """Получить дерево тем"""
        return await self._make_request("GET", "/api/v1/orator/topics/tree")

    async def get_user_topics(self) -> List[Dict[str, Any]]:
        """Получить темы пользователя"""
        return await self._make_request("GET", "/api/v1/orator/topics/user")

    # ============================================================================
    # ПОДБОР ПАР
    # ============================================================================

    async def find_candidates(self, match_request: Dict[str, Any]) -> Dict[str, Any]:
        """Найти кандидатов для пары"""
        return await self._make_request("POST", "/api/v1/orator/matching/find", json=match_request)

    # ============================================================================
    # ПАРЫ
    # ============================================================================

    async def create_pair(self, candidate_id: str) -> Dict[str, Any]:
        """Создать пару с кандидатом"""
        # Отключаем retry для создания пары, чтобы избежать дублирования
        return await self._make_request_without_retry(
            "POST", "/api/v1/orator/pairs/create", json={"candidate_id": candidate_id}
        )

    async def confirm_pair(self, pair_id: str) -> Dict[str, Any]:
        """Подтвердить пару"""
        return await self._make_request("POST", f"/api/v1/orator/pairs/{pair_id}/confirm")

    async def cancel_pair(self, pair_id: str) -> Dict[str, Any]:
        """Отменить пару"""
        return await self._make_request("POST", f"/api/v1/orator/pairs/{pair_id}/cancel")

    async def get_user_pairs(self) -> List[Dict[str, Any]]:
        """Получить пары пользователя"""
        return await self._make_request("GET", "/api/v1/orator/pairs")

    # ============================================================================
    # ОБРАТНАЯ СВЯЗЬ
    # ============================================================================

    async def create_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать обратную связь"""
        return await self._make_request("POST", "/api/v1/orator/feedback", json=feedback_data)

    async def get_received_feedback(self) -> List[Dict[str, Any]]:
        """Получить полученную обратную связь"""
        return await self._make_request("GET", "/api/v1/orator/feedback/received")

    async def get_given_feedback(self) -> List[Dict[str, Any]]:
        """Получить данную обратную связь"""
        return await self._make_request("GET", "/api/v1/orator/feedback/given")

    # ============================================================================
    # КОНТЕНТ БОТА
    # ============================================================================

    async def get_bot_content(self, content_key: str) -> Dict[str, Any]:
        """Получить контент бота"""
        return await self._make_request("GET", f"/api/v1/orator/content/{content_key}")

    async def get_exercises_by_topic(self, topic_id: str) -> Dict[str, Any]:
        """Получить упражнения по теме"""
        return await self._make_request("GET", f"/api/v1/orator/content/exercise/{topic_id}")

    # ============================================================================
    # НАСТРОЙКИ
    # ============================================================================

    async def get_user_settings(self) -> Dict[str, Any]:
        """Получить настройки пользователя"""
        return await self._make_request("GET", "/api/v1/settings")

    async def update_user_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Обновить настройки пользователя"""
        return await self._make_request("PUT", "/api/v1/settings", json=settings)

    async def reset_user_settings(self) -> Dict[str, str]:
        """Сбросить настройки пользователя"""
        return await self._make_request("DELETE", "/api/v1/settings")
