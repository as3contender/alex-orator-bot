#!/usr/bin/env python3
"""
Модуль безопасности для админ-панели
Включает безопасное хеширование паролей, защиту от брутфорса и другие меры безопасности
"""

import os
import bcrypt
import jwt
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from collections import defaultdict
import threading

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
try:
    from dotenv import load_dotenv

    # Загружаем deploy.env из корня проекта
    import os

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    deploy_env_path = os.path.join(project_root, "deployment", "deploy.env")

    if os.path.exists(deploy_env_path):
        load_dotenv(deploy_env_path)
        logger.info(f"✅ Переменные окружения загружены из {deploy_env_path}")
    else:
        load_dotenv()  # Fallback к .env в текущей директории
        logger.info("✅ Переменные окружения загружены из .env")
except ImportError:
    logger.warning("⚠️ python-dotenv не установлен, используем системные переменные окружения")


class BruteForceProtection:
    """Защита от брутфорс атак"""

    def __init__(self):
        self.login_attempts = defaultdict(list)
        self.lock = threading.Lock()
        self.max_attempts = int(os.getenv("MAX_LOGIN_ATTEMPTS", 5))
        self.timeout_minutes = int(os.getenv("LOGIN_TIMEOUT_MINUTES", 15))

    def is_blocked(self, username: str) -> bool:
        """Проверить, заблокирован ли пользователь"""
        with self.lock:
            attempts = self.login_attempts.get(username, [])
            if not attempts:
                return False

            # Удаляем старые попытки
            current_time = time.time()
            attempts = [attempt for attempt in attempts if current_time - attempt < self.timeout_minutes * 60]
            self.login_attempts[username] = attempts

            # Проверяем количество попыток
            if len(attempts) >= self.max_attempts:
                logger.warning(f"🚫 Пользователь {username} заблокирован из-за множественных попыток входа")
                return True

            return False

    def record_attempt(self, username: str, success: bool):
        """Записать попытку входа"""
        with self.lock:
            current_time = time.time()

            if success:
                # При успешном входе очищаем попытки
                self.login_attempts[username] = []
                logger.info(f"✅ Успешный вход пользователя {username}, попытки сброшены")
            else:
                # При неудачном входе добавляем попытку
                self.login_attempts[username].append(current_time)
                attempts_count = len(self.login_attempts[username])
                logger.warning(
                    f"❌ Неудачная попытка входа для {username} (попытка {attempts_count}/{self.max_attempts})"
                )

                if attempts_count >= self.max_attempts:
                    logger.error(f"🚫 Пользователь {username} заблокирован на {self.timeout_minutes} минут")


class PasswordSecurity:
    """Безопасная работа с паролями"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Безопасное хеширование пароля с использованием bcrypt"""
        try:
            rounds = int(os.getenv("BCRYPT_ROUNDS", 12))
            salt = bcrypt.gensalt(rounds=rounds)
            hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
            return hashed.decode("utf-8")
        except Exception as e:
            logger.error(f"Ошибка хеширования пароля: {e}")
            raise

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
        except Exception as e:
            logger.error(f"Ошибка проверки пароля: {e}")
            return False

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, str]:
        """Проверка сложности пароля"""
        if len(password) < 8:
            return False, "Пароль должен содержать минимум 8 символов"

        if not any(c.isupper() for c in password):
            return False, "Пароль должен содержать хотя бы одну заглавную букву"

        if not any(c.islower() for c in password):
            return False, "Пароль должен содержать хотя бы одну строчную букву"

        if not any(c.isdigit() for c in password):
            return False, "Пароль должен содержать хотя бы одну цифру"

        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            return False, "Пароль должен содержать хотя бы один специальный символ"

        return True, "Пароль соответствует требованиям безопасности"


class JWTManager:
    """Управление JWT токенами"""

    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY")
        if not self.secret_key or len(self.secret_key) < 32:
            logger.error("❌ JWT_SECRET_KEY не установлен или слишком короткий (минимум 32 символа)")
            raise ValueError("JWT_SECRET_KEY должен быть установлен и содержать минимум 32 символа")

        self.algorithm = "HS256"
        self.session_timeout = int(os.getenv("SESSION_TIMEOUT_MINUTES", 30))

    def create_token(self, username: str, role: str) -> str:
        """Создать JWT токен"""
        try:
            payload = {
                "username": username,
                "role": role,
                "exp": datetime.utcnow() + timedelta(minutes=self.session_timeout),
                "iat": datetime.utcnow(),
            }
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            logger.info(f"✅ JWT токен создан для пользователя {username}")
            return token
        except Exception as e:
            logger.error(f"Ошибка создания JWT токена: {e}")
            raise

    def verify_token(self, token: str) -> Optional[Dict]:
        """Проверить JWT токен"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            logger.info(f"✅ JWT токен проверен для пользователя {payload.get('username')}")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("❌ JWT токен истек")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"❌ Недействительный JWT токен: {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка проверки JWT токена: {e}")
            return None

    def refresh_token(self, token: str) -> Optional[str]:
        """Обновить JWT токен"""
        payload = self.verify_token(token)
        if payload:
            return self.create_token(payload["username"], payload["role"])
        return None


class SecurityManager:
    """Главный менеджер безопасности"""

    def __init__(self):
        self.brute_force_protection = BruteForceProtection()
        self.password_security = PasswordSecurity()
        self.jwt_manager = JWTManager()

        # Проверяем наличие необходимых переменных окружения
        self._validate_environment()

    def _validate_environment(self):
        """Проверка переменных окружения"""
        # Используем переменные из deploy.env
        required_vars = ["APP_DB_PASSWORD", "JWT_SECRET_KEY"]  # Из deploy.env  # Из deploy.env

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            logger.error(f"❌ Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
            logger.error("Проверьте файл deployment/deploy.env")
            raise ValueError(f"Отсутствуют переменные окружения: {missing_vars}")

        logger.info("✅ Все обязательные переменные окружения установлены")

    def authenticate_user(self, username: str, password: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Аутентификация пользователя

        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (успех, токен, роль)
        """
        # Проверяем блокировку
        if self.brute_force_protection.is_blocked(username):
            return False, None, None

        # Здесь будет логика аутентификации из БД
        # Пока возвращаем False для демонстрации
        success = False
        role = None

        if success:
            token = self.jwt_manager.create_token(username, role)
            self.brute_force_protection.record_attempt(username, True)
            return True, token, role
        else:
            self.brute_force_protection.record_attempt(username, False)
            return False, None, None

    def validate_session(self, token: str) -> Optional[Dict]:
        """Проверка сессии пользователя"""
        return self.jwt_manager.verify_token(token)

    def hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        return self.password_security.hash_password(password)

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return self.password_security.verify_password(password, hashed_password)

    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """Проверка сложности пароля"""
        return self.password_security.validate_password_strength(password)


# Глобальный экземпляр менеджера безопасности (ленивая инициализация)
_security_manager_instance = None


def get_security_manager():
    """Получить экземпляр менеджера безопасности"""
    global _security_manager_instance
    if _security_manager_instance is None:
        _security_manager_instance = SecurityManager()
    return _security_manager_instance


# Для обратной совместимости
security_manager = property(get_security_manager)
