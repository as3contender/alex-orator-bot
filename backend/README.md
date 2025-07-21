# CloverdashBot Backend

FastAPI приложение для интеллектуальной системы анализа данных.

## 🚀 Быстрый старт

### Локальная разработка
```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp env_example.txt .env
# Отредактировать .env файл

# Запуск
uvicorn main:app --reload
```

### Docker
```bash
# Сборка образа
docker build -t cloverdashbot-backend .

# Запуск контейнера
docker run -p 8000:8000 --env-file .env cloverdashbot-backend
```

## 📚 API Документация

После запуска приложения документация доступна по адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `DEBUG` | Режим отладки | `false` |
| `SECRET_KEY` | Секретный ключ | `your-secret-key-change-in-production` |
| `OPENAI_API_KEY` | API ключ OpenAI | - |
| `OPENAI_MODEL` | Модель OpenAI | `gpt-3.5-turbo` |
| `APP_DATABASE_URL` | URL базы данных приложения | - |
| `DATA_DATABASE_URL` | URL базы данных пользовательских данных | - |
| `JWT_SECRET_KEY` | Секретный ключ для JWT | - |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Время жизни токена (мин) | `30` |

## 🗂️ Структура проекта

```
backend/
├── main.py                 # Точка входа приложения
├── config/                 # Конфигурация
│   ├── __init__.py
│   └── settings.py        # Настройки приложения
├── api/                   # API эндпоинты
│   ├── __init__.py
│   ├── routes.py          # Главный роутер
│   ├── auth.py            # Аутентификация
│   ├── database.py        # Работа с данными
│   ├── health.py          # Health checks
│   └── user_settings.py   # Настройки пользователей
├── models/                # Pydantic модели
│   ├── __init__.py
│   ├── auth.py            # Модели аутентификации
│   ├── base.py            # Базовые модели
│   ├── database.py        # Модели базы данных
│   ├── llm.py             # Модели LLM
│   ├── telegram.py        # Модели Telegram
│   └── user_settings.py   # Модели настроек
├── services/              # Бизнес-логика
│   ├── __init__.py
│   ├── app_database.py    # Сервис приложения БД
│   ├── data_database.py   # Сервис данных БД
│   ├── llm_service.py     # Сервис LLM
│   ├── security.py        # Сервис безопасности
│   └── user_service.py    # Сервис пользователей
├── requirements.txt       # Зависимости
├── Dockerfile            # Docker образ
└── env_example.txt       # Пример конфигурации
```

## 🔒 Безопасность

- JWT аутентификация для всех API операций
- Хеширование паролей с использованием bcrypt
- Валидация SQL запросов (только SELECT)
- Защита от SQL инъекций через параметризованные запросы

## 📊 Health Checks

- `GET /health/` - Базовый health check
- `GET /health/info` - Детальная информация о состоянии
- `GET /health/ready` - Readiness check для Kubernetes
- `GET /health/live` - Liveness check для Kubernetes

## 🧪 Тестирование

```bash
# Запуск тестов
pytest

# Запуск с coverage
pytest --cov=.

# Запуск тестов с отчетом
pytest --cov=. --cov-report=html
```

## 📝 Логирование

Приложение использует структурированное логирование через Loguru. Логи сохраняются в файл `logs/backend.log` с ротацией по дням.

## 🔄 Миграции

База данных создается автоматически при первом запуске. Для production рекомендуется использовать Alembic для управления миграциями. 