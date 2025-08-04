# 🚀 CloverdashBot Template

Готовый архитектурный шаблон для создания интеллектуальных систем анализа данных через Telegram с использованием LLM.

## 🏗️ Архитектура

```
[Telegram Bot] <---> [FastAPI Backend] <---> [PostgreSQL + OpenAI]
                              |
                    [Разделенные базы данных]
```

## 🚀 Быстрый старт

### 1. Клонирование и настройка
```bash
git clone <your-repo> my-project
cd my-project

# Настройка переменных окружения
cp backend/.env.example backend/.env
cp telegram-bot/.env.example telegram-bot/.env
# Отредактировать .env файлы
```

### 2. Запуск локальной разработки
```bash
make local-up
```

### 3. Проверка работы
- Backend: http://localhost:8000/health
- Telegram Bot: Найдите вашего бота и отправьте `/start`

## 📦 Технологический стек

- **Backend**: FastAPI, PostgreSQL, OpenAI
- **Telegram Bot**: python-telegram-bot, aiohttp
- **Инфраструктура**: Docker, Docker Compose, Make

## 🗂️ Структура проекта

```
├── backend/                 # FastAPI приложение
├── telegram-bot/           # Telegram бот
├── deployment/             # Конфигурации развертывания
├── docs/                   # Документация
└── tests/                  # E2E тесты
```

## 📋 Доступные команды

### Telegram Bot
- `/start` - Начало работы
- `/help` - Справка
- `/tables` - Список доступных таблиц
- `/sample` - Примеры запросов
- `/settings` - Настройки пользователя
- `/en`, `/ru` - Быстрая смена языка

### Make команды
```bash
make local-up          # Запуск локальной разработки
make local-down        # Остановка локальной разработки
make logs              # Просмотр логов
make test              # Запуск тестов
make clean             # Очистка контейнеров
```

## 🔧 Конфигурация

### Backend (.env)
```env
OPENAI_API_KEY=your_openai_api_key_here
APP_DATABASE_URL=postgresql://user:pass@localhost:5432/app_db
SECRET_KEY=your-secret-key-here
```

### Telegram Bot (.env)
```env
TELEGRAM_TOKEN=your_telegram_bot_token
BACKEND_URL=http://localhost:8000
```

## 📚 Документация

- [Архитектурное описание](cloverdash-template-description.md)
- [Backend API](backend/README.md)
- [Telegram Bot](telegram-bot/README.md)
- [Развертывание](deployment/README.md)

## 🔒 Безопасность

- JWT аутентификация
- Хеширование паролей (bcrypt)
- Защита от SQL инъекций
- Только SELECT запросы к пользовательским данным

## 🎯 Примеры применения

- Аналитика продаж
- HR аналитика
- Финансовая аналитика
- IoT мониторинг

## 📄 Лицензия

MIT License 