from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

from config.settings import settings

# Настройка хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Настройка JWT
security = HTTPBearer()


class SecurityService:
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.jwt_access_token_expire_minutes

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Хеширование пароля"""
        return pwd_context.hash(password)

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Создание JWT токена"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[dict]:
        """Проверка JWT токена"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            role: str = payload.get("role", "user")
            if user_id is None:
                return None
            return {"user_id": user_id, "role": role}
        except JWTError:
            return None

    async def get_current_user_id(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
        """Получение ID текущего пользователя из токена"""
        token = credentials.credentials
        token_data = self.verify_token(token)
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token_data["user_id"]

    def get_current_user_role(self, token: str) -> str:
        """Получение роли текущего пользователя из токена"""
        token_data = self.verify_token(token)
        if token_data is None:
            return "user"
        return token_data["role"]

    def create_telegram_token(self, telegram_id: str) -> str:
        """Создание токена для Telegram пользователя"""
        return self.create_access_token(data={"sub": f"telegram_{telegram_id}"})


# Создание экземпляра сервиса
security_service = SecurityService()
