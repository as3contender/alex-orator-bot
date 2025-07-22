import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from config import API_TIMEOUT, API_RETRY_ATTEMPTS, API_RETRY_DELAY
from exceptions import BackendConnectionError, AuthenticationError
from models import TableInfo, UserSettings, SampleData


class APIClient:
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
                async with session.get(f"{self.base_url}/health/") as response:
                    if response.status == 200:
                        logger.info("Backend connection successful")
                        return True
                    else:
                        raise BackendConnectionError(f"Backend health check failed: {response.status}")
        except Exception as e:
            logger.error(f"Backend connection check failed: {e}")
            raise BackendConnectionError(f"Failed to connect to backend: {e}")

    @retry(
        stop=stop_after_attempt(API_RETRY_ATTEMPTS), wait=wait_exponential(multiplier=1, min=API_RETRY_DELAY, max=10)
    )
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Выполнение HTTP запроса с retry логикой"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")

        url = f"{self.base_url}{endpoint}"

        # Добавляем заголовки авторизации
        headers = kwargs.get("headers", {})
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        kwargs["headers"] = headers

        try:
            async with self.session.request(method, url, **kwargs) as response:
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

    async def get_tables(self) -> List[TableInfo]:
        """Получение списка таблиц"""
        response = await self._make_request("GET", "/api/v1/database/tables")
        return [TableInfo(**table) for table in response]

    async def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Получение информации о колонках таблицы"""
        return await self._make_request("GET", f"/api/v1/database/tables/{table_name}/columns")

    async def execute_sql_query(self, sql: str) -> Dict[str, Any]:
        """Выполнение SQL запроса"""
        data = {"sql": sql}
        return await self._make_request("POST", "/api/v1/database/query", json=data)

    async def get_sample_data(self, table_name: str, limit: int = 10) -> SampleData:
        """Получение примера данных из таблицы"""
        response = await self._make_request("GET", f"/api/v1/database/sample-data/{table_name}?limit={limit}")
        return SampleData(**response)

    async def get_user_settings(self) -> UserSettings:
        """Получение настроек пользователя"""
        response = await self._make_request("GET", "/api/v1/settings/")
        return UserSettings(**response)

    async def update_user_settings(self, settings: Dict[str, Any]) -> UserSettings:
        """Обновление настроек пользователя"""
        response = await self._make_request("PUT", "/api/v1/settings/", json=settings)
        return UserSettings(**response)

    async def reset_user_settings(self) -> Dict[str, str]:
        """Сброс настроек пользователя"""
        return await self._make_request("POST", "/api/v1/settings/reset")

    async def get_database_schema(self) -> Dict[str, Any]:
        """Получение схемы базы данных"""
        tables = await self.get_tables()
        schema = {"tables": []}

        for table in tables:
            columns = await self.get_table_columns(table.name)
            table_info = {"name": table.name, "description": table.description, "columns": columns}
            schema["tables"].append(table_info)

        return schema
