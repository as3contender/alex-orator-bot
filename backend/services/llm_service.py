import openai
from typing import List, Dict, Any
from loguru import logger

from config.settings import settings
from models.llm import SQLGenerationRequest, SQLGenerationResponse


class LLMService:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.max_tokens = settings.openai_max_tokens
        self.temperature = settings.openai_temperature

    async def check_connection(self):
        """Проверка подключения к OpenAI"""
        try:
            # Простой тестовый запрос
            response = await self.client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": "Hello"}], max_tokens=10
            )
            logger.info("OpenAI connection check successful")
        except Exception as e:
            logger.error(f"OpenAI connection check failed: {e}")
            raise

    def _build_system_prompt(self, tables_info: List[Dict[str, Any]], user_language: str = "ru") -> str:
        """Построение системного промпта"""
        if user_language == "ru":
            prompt = """Ты - эксперт по SQL и анализу данных. Твоя задача - генерировать корректные SQL запросы на основе запросов пользователя на естественном языке.

Правила:
1. Генерируй ТОЛЬКО SQL запросы, начинающиеся с SELECT
2. Не используй INSERT, UPDATE, DELETE, DROP, CREATE
3. Используй только таблицы и колонки из предоставленной схемы
4. Если запрос неоднозначен, уточни у пользователя
5. Объясняй логику запроса на русском языке

Доступные таблицы и колонки:
"""
        else:
            prompt = """You are an expert in SQL and data analysis. Your task is to generate correct SQL queries based on user requests in natural language.

Rules:
1. Generate ONLY SQL queries starting with SELECT
2. Do not use INSERT, UPDATE, DELETE, DROP, CREATE
3. Use only tables and columns from the provided schema
4. If the query is ambiguous, ask the user for clarification
5. Explain the query logic in English

Available tables and columns:
"""

        # Добавляем информацию о таблицах
        for table_info in tables_info:
            prompt += f"\nТаблица: {table_info['name']}"
            if table_info.get("description"):
                prompt += f" - {table_info['description']}"

            for column in table_info.get("columns", []):
                prompt += f"\n  - {column['name']} ({column['data_type']})"
                if column.get("description"):
                    prompt += f" - {column['description']}"
            prompt += "\n"

        prompt += '\nОтвечай в формате JSON:\n{\n  "sql": "SELECT ...",\n  "explanation": "Объяснение запроса"\n}'

        return prompt

    async def generate_sql_query(
        self, user_query: str, tables_info: List[Dict[str, Any]], user_language: str = "ru"
    ) -> SQLGenerationResponse:
        """Генерация SQL запроса из естественного языка"""
        try:
            system_prompt = self._build_system_prompt(tables_info, user_language)

            messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_query}]

            response = await self.client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=self.max_tokens, temperature=self.temperature
            )

            content = response.choices[0].message.content
            logger.info(f"OpenAI response: {content}")

            # Парсим JSON ответ
            import json

            try:
                result = json.loads(content)
                sql = result.get("sql", "")
                explanation = result.get("explanation", "")
            except json.JSONDecodeError:
                # Если не удалось распарсить JSON, извлекаем SQL из текста
                sql = self._extract_sql_from_text(content)
                explanation = content

            return SQLGenerationResponse(
                sql=sql,
                explanation=explanation,
                confidence=0.8,  # TODO: реализовать оценку уверенности
                suggested_improvements=None,
            )

        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            raise

    def _extract_sql_from_text(self, text: str) -> str:
        """Извлечение SQL из текста ответа"""
        # Простая эвристика для извлечения SQL
        import re

        # Ищем SQL запросы
        sql_pattern = r"SELECT\s+.*?(?:;|$)"
        matches = re.findall(sql_pattern, text, re.IGNORECASE | re.DOTALL)

        if matches:
            return matches[0].strip()

        # Если не нашли, возвращаем весь текст
        return text

    async def validate_sql_query(self, sql: str) -> bool:
        """Валидация SQL запроса"""
        # Проверяем, что запрос начинается с SELECT
        if not sql.strip().upper().startswith("SELECT"):
            return False

        # Проверяем на наличие запрещенных операций
        forbidden_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"]
        sql_upper = sql.upper()

        for keyword in forbidden_keywords:
            if keyword in sql_upper:
                return False

        return True

    async def explain_sql_query(self, sql: str, user_language: str = "ru") -> str:
        """Объяснение SQL запроса на естественном языке"""
        try:
            if user_language == "ru":
                prompt = f"Объясни этот SQL запрос простыми словами на русском языке:\n\n{sql}"
            else:
                prompt = f"Explain this SQL query in simple terms in English:\n\n{sql}"

            response = await self.client.chat.completions.create(
                model=self.model, messages=[{"role": "user", "content": prompt}], max_tokens=300, temperature=0.3
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"SQL explanation failed: {e}")
            return "Не удалось объяснить запрос"


# Создание экземпляра сервиса
llm_service = LLMService()
