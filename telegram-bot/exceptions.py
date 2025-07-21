class CloverdashBotException(Exception):
    """Базовое исключение для CloverdashBot"""

    pass


class BackendConnectionError(CloverdashBotException):
    """Ошибка подключения к backend"""

    pass


class AuthenticationError(CloverdashBotException):
    """Ошибка аутентификации"""

    pass


class QueryProcessingError(CloverdashBotException):
    """Ошибка обработки запроса"""

    pass


class DatabaseError(CloverdashBotException):
    """Ошибка базы данных"""

    pass


class LLMError(CloverdashBotException):
    """Ошибка LLM сервиса"""

    pass


class ValidationError(CloverdashBotException):
    """Ошибка валидации данных"""

    pass


class RateLimitError(CloverdashBotException):
    """Ошибка превышения лимита запросов"""

    pass
