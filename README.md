# 🎯 Alex Orator Bot

**Telegram бот для подбора пар для тренировки ораторского искусства с интеллектуальным алгоритмом матчинга.**

## 🏗️ Архитектура

```
[Telegram Bot] <---> [FastAPI Backend] <---> [PostgreSQL]
                              |
                    [Worker для отправки сообщений]
```

## 🚀 Быстрый старт

### 1. Клонирование и настройка
```bash
git clone <your-repo> alex-orator-bot
cd alex-orator-bot

# Настройка переменных окружения
cp env.example .env
cp backend/env_example.txt backend/.env
cp telegram-bot/env_example.txt telegram-bot/.env
# Отредактировать .env файлы
```

### 2. Запуск локальной разработки
```bash
docker-compose -f docker-compose.local.yml up -d
```

### 3. Проверка работы
- **Backend**: http://localhost:8000/health
- **Telegram Bot**: Найдите вашего бота и отправьте `/start`

## 📦 Технологический стек

- **Backend**: FastAPI, PostgreSQL, SQLAlchemy
- **Telegram Bot**: python-telegram-bot, aiohttp
- **Worker**: Асинхронная отправка сообщений
- **Инфраструктура**: Docker, Docker Compose, Make

## 🗂️ Структура проекта

```
alex-orator-bot/
├── backend/                 # FastAPI приложение
│   ├── main.py             # Точка входа приложения
│   ├── config/             # Конфигурация
│   ├── api/                # API эндпоинты
│   │   ├── auth.py         # Аутентификация
│   │   ├── health.py       # Health checks
│   │   ├── user_settings.py # Настройки пользователей
│   │   └── orator/         # API для Alex Orator Bot
│   │       ├── profiles.py # Профили пользователей
│   │       ├── weeks.py    # Регистрации на недели
│   │       ├── topics.py   # Темы для тренировки
│   │       ├── matching.py # Поиск кандидатов
│   │       ├── pairs.py    # Управление парами
│   │       ├── feedback.py # Обратная связь
│   │       ├── content.py  # Контент бота
│   │       └── settings.py # Настройки системы
│   ├── models/             # Pydantic модели
│   │   ├── auth.py         # Модели аутентификации
│   │   ├── base.py         # Базовые модели
│   │   ├── database.py     # Модели базы данных
│   │   ├── llm.py          # Модели LLM
│   │   ├── telegram.py     # Модели Telegram
│   │   ├── user_settings.py # Модели настроек
│   │   └── orator/         # Модели для Alex Orator Bot
│   │       ├── users.py    # Модели пользователей
│   │       ├── weeks.py    # Модели регистраций
│   │       ├── topics.py   # Модели тем
│   │       ├── pairs.py    # Модели пар
│   │       ├── feedback.py # Модели обратной связи
│   │       ├── matching.py # Модели матчинга
│   │       ├── content.py  # Модели контента
│   │       ├── settings.py # Модели настроек
│   │       ├── enums.py    # Перечисления
│   │       └── message_queue.py # Модели очереди сообщений
│   ├── services/           # Бизнес-логика
│   │   ├── app_database.py # Сервис приложения БД
│   │   ├── orator_database.py # Сервис Alex Orator БД
│   │   ├── matching_service.py # Сервис матчинга
│   │   ├── message_queue_service.py # Сервис очереди сообщений
│   │   ├── user_service.py # Сервис пользователей
│   │   └── security.py     # Сервис безопасности
│   ├── texts/              # Текстовые файлы контента
│   ├── migrations/         # SQL миграции
│   ├── tests/              # Тесты
│   ├── logs/               # Логи
│   ├── content_parser.py   # Парсер контента
│   ├── load_bot_content.py # Загрузчик контента
│   ├── requirements.txt    # Зависимости
│   ├── Dockerfile          # Docker образ
│   └── env_example.txt     # Пример конфигурации
├── telegram-bot/           # Telegram бот
│   ├── orator_bot.py       # Основной файл бота
│   ├── orator_api_client.py # API клиент для backend
│   ├── orator_translations.py # Переводы (RU/EN)
│   ├── bot_content_manager.py # Менеджер контента
│   ├── handlers/           # Обработчики команд
│   │   ├── base_handler.py # Базовый обработчик
│   │   ├── command_handler.py # Обработчики команд
│   │   ├── callback_handler.py # Обработчики callback
│   │   ├── registration_handler.py # Регистрация
│   │   ├── topics_handler.py # Темы
│   │   ├── pairs_handler.py # Пары
│   │   └── feedback_handler.py # Обратная связь
│   ├── config.py           # Конфигурация
│   ├── exceptions.py       # Исключения
│   ├── error_handler.py    # Обработка ошибок
│   ├── test_orator_bot.py  # Тестовый скрипт
│   ├── requirements.txt    # Зависимости
│   ├── Dockerfile          # Docker образ
│   └── env_example.txt     # Пример конфигурации
├── worker/                 # Worker для отправки сообщений
│   ├── send_worker.py      # Основной worker
│   ├── db.py               # Подключение к БД
│   ├── requirements.txt    # Зависимости
│   └── Dockerfile          # Docker образ
├── deployment/             # Конфигурации развертывания
│   ├── deploy_alex_orator.sh # Скрипт деплоя
│   ├── init-orator-app-db.sql # Инициализация БД
│   ├── bot_content_dump.sql # Дамп контента
│   ├── export_data_dumps.py # Экспорт данных
│   ├── deploy.env.example  # Пример конфигурации деплоя
│   └── README.md           # Документация по деплою
├── docs/                   # Документация
│   ├── technical-requirements.md # Техническое задание
│   └── todo-list.md        # Список задач
├── logs/                   # Логи приложений
├── docker-compose.yml      # Production конфигурация
├── docker-compose.local.yml # Локальная разработка
├── requirements.txt        # Зависимости
├── env.example             # Пример конфигурации
├── start.sh                # Скрипт запуска
├── Makefile                # Команды управления
├── README.md               # Эта документация
├── DOCKER_README.md        # Документация по Docker
├── SECURITY.md             # Политика безопасности
├── SETUP_COMPLETE.md       # Инструкции по настройке
├── implementation_plan.md  # План реализации
└── generate_keys.py        # Генератор ключей
```

## 📋 Основные функции

### Telegram Bot
- `/start` - Начало работы с ботом
- `/register` - Регистрация на неделю
- `/topics` - Выбор тем для тренировки
- `/find` - Поиск кандидатов для пары
- `/pairs` - Просмотр своих пар
- `/feedback` - Обратная связь
- `/profile` - Профиль пользователя
- `/stats` - Статистика тренировок
- `/help` - Справка

### Make команды
```bash
make local-up          # Запуск локальной разработки
make local-down        # Остановка локальной разработки
make logs              # Просмотр логов
make test              # Запуск тестов
make clean             # Очистка контейнеров
```

## 🔧 Конфигурация

### Основные переменные (.env)
```env
# Telegram Bot
BOT_TOKEN=your_telegram_bot_token_here

# Backend API
BACKEND_URL=http://localhost:8000
API_TIMEOUT=30
API_RETRY_ATTEMPTS=3
API_RETRY_DELAY=1

# Базы данных
APP_DATABASE_URL=postgresql://user:local_password@localhost:5432/app_db

# JWT и безопасность
JWT_SECRET_KEY=your-jwt-secret-key-here
SECRET_KEY=your-secret-key-here

# Логирование
LOG_LEVEL=INFO
DEBUG=false

# Настройки бота
DEFAULT_LANGUAGE=ru
MAX_PAIRS_PER_USER=3
DEFAULT_MATCHING_LIMIT=5
```

## 📚 Документация

- [Техническое задание](docs/technical-requirements.md)
- [Список задач](docs/todo-list.md)
- [Backend API](backend/README.md)
- [Telegram Bot](telegram-bot/README.md)
- [Развертывание](deployment/README.md)
- [Docker](DOCKER_README.md)

## 🔒 Безопасность

- JWT аутентификация через Telegram
- Валидация всех входных данных
- Обработка ошибок без утечки информации

## 🎯 Основные возможности

### Подбор пар
- Интеллектуальный алгоритм матчинга по времени и темам
- Автоматическое уведомление о новых парах
- Подтверждение/отклонение предложений

### Управление регистрациями
- Регистрация на текущую или следующую неделю
- Выбор предпочтительного времени
- Выбор тем для тренировки

### Обратная связь
- Система отзывов о партнерах
- Требование обратной связи для повторной регистрации
- История всех отзывов

### Мультиязычность
- Поддержка русского и английского языков
- Быстрое переключение языков
- Автоматическое определение языка пользователя

## 🚀 Дополнительные возможности

### Скрипты запуска
- `start.sh` - для Linux/Mac
- `start_docker.bat` - для Windows
- `start_docker.ps1` - для PowerShell

### Админ-панель
- Управление пользователями и ролями
- Система упражнений и контента
- Администрирование образовательных платформ

## 📄 Лицензия

MIT License