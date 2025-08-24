import hashlib
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import jwt
from database import get_db
from sqlalchemy import text

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения из .env файла
try:
    from dotenv import load_dotenv

    load_dotenv()
    print("✅ Переменные окружения загружены в auth.py")
except ImportError:
    print("⚠️ python-dotenv не установлен, используем системные переменные окружения")


def get_sqlalchemy_engine():
    """Получить SQLAlchemy engine для подключения к БД"""
    try:
        from sqlalchemy import create_engine

        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5434")
        db_name = os.getenv("DB_NAME", "app_db")
        db_user = os.getenv("DB_USER", "alex_orator")
        db_password = os.getenv("APP_DB_PASSWORD")  # Из deploy.env

        if not db_password:
            logger.error("APP_DB_PASSWORD не установлен в переменных окружения")
            return None

        from urllib.parse import quote_plus

        encoded_password = quote_plus(db_password)
        database_url = f"postgresql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"
        engine = create_engine(database_url)
        return engine
    except Exception as e:
        logger.error(f"Ошибка создания SQLAlchemy engine: {e}")
        return None


def authenticate_user(username, password):
    """Аутентификация пользователя из БД"""
    try:
        # Сначала проверяем пользователей из БД
        engine = get_sqlalchemy_engine()

        if engine:
            # Проверяем существование таблицы admin_users
            check_admin_table_query = text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'admin_users'
                );
            """
            )

            # Проверяем существование таблицы users
            check_users_table_query = text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                );
            """
            )

            with engine.connect() as conn:
                # Проверяем таблицу admin_users
                result = conn.execute(check_admin_table_query)
                admin_table_exists = result.scalar()

                if admin_table_exists:
                    # Ищем пользователя в таблице admin_users
                    admin_query = text(
                        """
                        SELECT hashed_password FROM admin_users 
                        WHERE username = :username AND is_active = true
                    """
                    )

                    result = conn.execute(admin_query, {"username": username})
                    row = result.fetchone()

                    if row:
                        # Проверяем пароль с использованием bcrypt
                        hashed_password = row[0]
                        try:
                            from security import security_manager

                            if security_manager.verify_password(password, hashed_password):
                                logger.info(f"Успешная авторизация администратора {username} из БД")
                                return True
                            else:
                                logger.warning(f"Неверный пароль для администратора {username} из БД")
                                return False
                        except ImportError:
                            # Fallback к SHA256 если модуль security недоступен
                            if hashed_password == hashlib.sha256(password.encode()).hexdigest():
                                logger.info(f"Успешная авторизация администратора {username} из БД (SHA256)")
                                return True
                            else:
                                logger.warning(f"Неверный пароль для администратора {username} из БД")
                                return False

                # Проверяем таблицу users
                result = conn.execute(check_users_table_query)
                users_table_exists = result.scalar()

                if users_table_exists:
                    # Ищем пользователя в таблице users
                    user_query = text(
                        """
                        SELECT password FROM users 
                        WHERE username = :username AND is_active = true
                    """
                    )

                    result = conn.execute(user_query, {"username": username})
                    row = result.fetchone()

                    if row:
                        # Проверяем пароль с использованием bcrypt
                        hashed_password = row[0]
                        if hashed_password:
                            try:
                                from security import security_manager

                                if security_manager.verify_password(password, hashed_password):
                                    logger.info(f"Успешная авторизация пользователя {username} из БД")
                                    return True
                                else:
                                    logger.warning(f"Неверный пароль для пользователя {username} из БД")
                                    return False
                            except ImportError:
                                # Fallback к SHA256 если модуль security недоступен
                                if hashed_password == hashlib.sha256(password.encode()).hexdigest():
                                    logger.info(f"Успешная авторизация пользователя {username} из БД (SHA256)")
                                    return True
                                else:
                                    logger.warning(f"Неверный пароль для пользователя {username} из БД")
                                    return False

        # Если пользователь не найден в БД
        logger.warning(f"Пользователь {username} не найден в базе данных")
        return False

    except Exception as e:
        logger.error(f"Ошибка при аутентификации пользователя {username}: {e}", exc_info=True)
        return False


def get_user_role(username):
    """Получить роль пользователя из БД или системных настроек"""
    try:
        # Сначала проверяем пользователей из БД
        engine = get_sqlalchemy_engine()

        if engine:
            # Проверяем существование таблицы admin_users
            check_admin_table_query = text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'admin_users'
                );
            """
            )

            # Проверяем существование таблицы users
            check_users_table_query = text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                );
            """
            )

            with engine.connect() as conn:
                # Проверяем таблицу admin_users
                result = conn.execute(check_admin_table_query)
                admin_table_exists = result.scalar()

                if admin_table_exists:
                    # Ищем пользователя в таблице admin_users
                    admin_query = text(
                        """
                        SELECT full_name, role FROM admin_users 
                        WHERE username = :username AND is_active = true
                    """
                    )

                    result = conn.execute(admin_query, {"username": username})
                    row = result.fetchone()

                    if row:
                        full_name = row[0]
                        role = row[1]
                        # Возвращаем роль из БД, но делаем её красивой для отображения
                        if role == "super_admin":
                            return "Супер-администратор"
                        elif role == "admin":
                            return "Администратор"
                        elif role == "moderator":
                            return "Модератор"
                        else:
                            return role.capitalize()  # Первая буква заглавная

                # Проверяем таблицу users
                result = conn.execute(check_users_table_query)
                users_table_exists = result.scalar()

                if users_table_exists:
                    # Проверяем, есть ли колонка role в таблице users
                    check_role_column_query = text(
                        """
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns 
                            WHERE table_schema = 'public' 
                            AND table_name = 'users' 
                            AND column_name = 'role'
                        );
                    """
                    )

                    role_column_exists = conn.execute(check_role_column_query).scalar()

                    if role_column_exists:
                        # Ищем пользователя в таблице users с ролью
                        user_query = text(
                            """
                            SELECT first_name, last_name, role FROM users 
                            WHERE username = :username AND is_active = true
                        """
                        )

                        result = conn.execute(user_query, {"username": username})
                        row = result.fetchone()

                        if row:
                            first_name = row[0]
                            last_name = row[1]
                            role = row[2]
                            full_name = f"{first_name or ''} {last_name or ''}".strip()

                            # Возвращаем роль из БД, но делаем её красивой для отображения
                            if role == "super_admin":
                                return "Супер-администратор"
                            elif role == "admin":
                                return "Администратор"
                            elif role == "moderator":
                                return "Модератор"
                            elif role == "user":
                                return "Пользователь"
                            else:
                                return role.capitalize()  # Первая буква заглавная
                    else:
                        # Ищем пользователя в таблице users без колонки role
                        user_query = text(
                            """
                            SELECT first_name, last_name FROM users 
                            WHERE username = :username AND is_active = true
                        """
                        )

                        result = conn.execute(user_query, {"username": username})
                        row = result.fetchone()

                        if row:
                            first_name = row[0]
                            last_name = row[1]
                            full_name = f"{first_name or ''} {last_name or ''}".strip()
                            if full_name:
                                return "Пользователь"
                            else:
                                return "Пользователь"

        # Если пользователь не найден в БД
        logger.warning(f"Пользователь {username} не найден в базе данных")
        return "Неизвестно"

    except Exception as e:
        logger.error(f"Ошибка при получении роли пользователя {username}: {e}", exc_info=True)
        return "Неизвестно"


def get_user_info(username):
    """Получить полную информацию о пользователе"""
    try:
        engine = get_sqlalchemy_engine()

        if engine:
            # Проверяем таблицу admin_users
            check_admin_table_query = text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'admin_users'
                );
            """
            )

            with engine.connect() as conn:
                result = conn.execute(check_admin_table_query)
                admin_table_exists = result.scalar()

                if admin_table_exists:
                    # Ищем пользователя в таблице admin_users
                    admin_query = text(
                        """
                        SELECT id, username, full_name, role, is_active, last_login
                        FROM admin_users 
                        WHERE username = :username AND is_active = true
                    """
                    )

                    result = conn.execute(admin_query, {"username": username})
                    row = result.fetchone()

                    if row:
                        # Определяем тип пользователя на основе роли из БД
                        role = row[3]
                        if role in ["super_admin", "admin", "moderator"]:
                            user_type = "admin"
                        else:
                            user_type = "user"

                        return {
                            "id": row[0],
                            "username": row[1],
                            "full_name": row[2],
                            "role": row[3],
                            "is_active": row[4],
                            "last_login": row[5],
                            "user_type": user_type,
                        }

            # Проверяем таблицу users
            check_users_table_query = text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                );
            """
            )

            with engine.connect() as conn:
                result = conn.execute(check_users_table_query)
                users_table_exists = result.scalar()

                if users_table_exists:
                    # Ищем пользователя в таблице users
                    user_query = text(
                        """
                        SELECT id, username, first_name, last_name, is_active, created_at, role
                        FROM users 
                        WHERE username = :username AND is_active = true
                    """
                    )

                    result = conn.execute(user_query, {"username": username})
                    row = result.fetchone()

                    if row:
                        full_name = f"{row[2] or ''} {row[3] or ''}".strip()

                        # Получаем роль пользователя из БД
                        user_role = row[6] if len(row) > 6 else "user"

                        # Определяем тип пользователя на основе роли
                        if user_role in ["super_admin", "admin", "moderator"]:
                            user_type = "admin"
                        else:
                            user_type = "user"

                        return {
                            "id": row[0],
                            "username": row[1],
                            "full_name": full_name or row[1],
                            "role": user_role,  # Используем реальную роль из БД
                            "is_active": row[4],
                            "last_login": None,
                            "created_at": row[5],
                            "user_type": user_type,
                        }

        # Если пользователь не найден в БД
        logger.warning(f"Пользователь {username} не найден в базе данных")
        return None

    except Exception as e:
        logger.error(f"Ошибка при получении информации о пользователе {username}: {e}", exc_info=True)
        return None


# Сохраняем существующие функции для совместимости
class AdminAuth:
    def __init__(self):
        self.secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    def _hash_password(self, password: str) -> str:
        """Хеширование пароля"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверка пароля"""
        return self._hash_password(plain_password) == hashed_password

    def authenticate_admin(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Аутентификация администратора"""
        try:
            # Получаем экземпляр базы данных
            db = get_db()

            # Получаем администратора из базы данных
            admin = db.get_admin_by_username(username)
            if not admin:
                return None

            # Проверяем пароль
            if not self.verify_password(password, admin["hashed_password"]):
                return None

            # Обновляем время последнего входа
            db.update_admin_last_login(username)

            return {
                "username": admin["username"],
                "full_name": admin["full_name"],
                "role": admin["role"],
                "id": admin["id"],
                "user_type": "admin",  # Тип пользователя - администратор
            }
        except Exception as e:
            print(f"❌ Ошибка аутентификации: {e}")
            return None

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Аутентификация обычного пользователя"""
        try:
            # Получаем экземпляр базы данных
            db = get_db()

            # Получаем пользователя из таблицы users
            user = db.get_user_by_username(username)
            if not user:
                return None

            # Проверяем пароль
            if not self.verify_password(password, user["password"]):
                return None

            return {
                "username": user["username"],
                "full_name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip() or user["username"],
                "role": "user",  # Роль обычного пользователя
                "id": user["id"],
                "user_type": "user",  # Тип пользователя - обычный пользователь
            }
        except Exception as e:
            print(f"❌ Ошибка аутентификации пользователя: {e}")
            return None

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Универсальная аутентификация - проверяет и администраторов, и пользователей"""
        try:
            # Сначала пробуем найти администратора
            admin_result = self.authenticate_admin(username, password)
            if admin_result:
                return admin_result

            # Если не найден администратор, пробуем найти обычного пользователя
            user_result = self.authenticate_user(username, password)
            if user_result:
                return user_result

            return None
        except Exception as e:
            print(f"❌ Ошибка универсальной аутентификации: {e}")
            return None

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Создание JWT токена"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Проверка JWT токена"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None

    def get_current_admin(self, token: str) -> Optional[Dict[str, Any]]:
        """Получение текущего администратора по токену"""
        try:
            payload = self.verify_token(token)
            if payload is None:
                return None

            username = payload.get("sub")
            if username is None:
                return None

            # Получаем актуальные данные из базы данных
            db = get_db()
            admin = db.get_admin_by_username(username)
            if not admin:
                return None

            return {
                "username": admin["username"],
                "full_name": admin["full_name"],
                "role": admin["role"],
                "id": admin["id"],
            }
        except Exception as e:
            print(f"❌ Ошибка получения текущего администратора: {e}")
            return None


# Создание глобального экземпляра
auth = AdminAuth()


def get_auth():
    """Получить экземпляр аутентификации"""
    return auth


def hash_password(password: str) -> str:
    """Хеширование пароля"""
    return auth._hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return auth.verify_password(plain_password, hashed_password)


def create_default_admin():
    """Создание администратора по умолчанию"""
    try:
        db = get_db()

        # Проверяем, существует ли уже администратор
        existing_admin = db.get_admin_by_username("admin")
        if existing_admin:
            print("✅ Администратор по умолчанию уже существует")
            return existing_admin

        # Создаем администратора по умолчанию
        hashed_password = hash_password("admin123")
        admin = db.create_admin_user(
            username="admin", hashed_password=hashed_password, full_name="Администратор", role="super_admin"
        )

        if admin:
            print("✅ Администратор по умолчанию успешно создан")
            return admin
        else:
            print("❌ Ошибка создания администратора по умолчанию")
            return None

    except Exception as e:
        print(f"❌ Ошибка создания администратора по умолчанию: {e}")
        return None

    return auth._hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return auth.verify_password(plain_password, hashed_password)


def create_default_admin():
    """Создание администратора по умолчанию"""
    try:
        db = get_db()

        # Проверяем, существует ли уже администратор
        existing_admin = db.get_admin_by_username("admin")
        if existing_admin:
            print("✅ Администратор по умолчанию уже существует")
            return existing_admin

        # Создаем администратора по умолчанию
        hashed_password = hash_password("admin123")
        admin = db.create_admin_user(
            username="admin", hashed_password=hashed_password, full_name="Администратор", role="super_admin"
        )

        if admin:
            print("✅ Администратор по умолчанию успешно создан")
            return admin
        else:
            print("❌ Ошибка создания администратора по умолчанию")
            return None

    except Exception as e:
        print(f"❌ Ошибка создания администратора по умолчанию: {e}")
        return None
