# 🐳 Docker развертывание Alex Orator Bot

## 📋 Обзор

Этот проект использует Docker Compose для локальной разработки и тестирования Alex Orator Bot. Система включает в себя:

- **2 базы данных PostgreSQL** (приложение и данные)
- **Backend API** (FastAPI)
- **Telegram Bot** (Alex Orator Bot)

## 🏗️ Архитектура

### Сервисы:
1. **app-db** - PostgreSQL для приложения (порт 5432)
2. **data-db** - PostgreSQL для пользовательских данных (порт 5433)
3. **backend** - FastAPI backend (порт 8000)
4. **orator-bot** - Telegram бот

### Сети:
- `alex-orator-local-network` - внутренняя сеть для всех сервисов

### Тома:
- `alex-orator-app-db-data-local` - данные приложения
- `alex-orator-data-db-data-local` - пользовательские данные

## 🚀 Быстрый старт

### 1. Подготовка
```bash
# Клонируйте репозиторий
git clone <repository-url>
cd alex-orator-bot

# Скопируйте файл переменных окружения
cp env.example .env

# Отредактируйте .env файл
nano .env
```

### 2. Настройка переменных окружения
```env
# Обязательные
BOT_TOKEN=your_telegram_bot_token_here
JWT_SECRET_KEY=your-jwt-secret-key-here
SECRET_KEY=your-secret-key-here

# Опциональные
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Запуск
```bash
# Запуск всех сервисов
docker-compose -f docker-compose.local.yml up -d

# Просмотр логов
docker-compose -f docker-compose.local.yml logs -f

# Остановка
docker-compose -f docker-compose.local.yml down
```

## 🔧 Команды управления

### Основные команды:
```bash
# Запуск в фоновом режиме
docker-compose -f docker-compose.local.yml up -d

# Запуск с пересборкой
docker-compose -f docker-compose.local.yml up --build -d

# Просмотр логов всех сервисов
docker-compose -f docker-compose.local.yml logs -f

# Просмотр логов конкретного сервиса
docker-compose -f docker-compose.local.yml logs -f orator-bot
docker-compose -f docker-compose.local.yml logs -f backend

# Остановка всех сервисов
docker-compose -f docker-compose.local.yml down

# Остановка с удалением томов
docker-compose -f docker-compose.local.yml down -v

# Перезапуск конкретного сервиса
docker-compose -f docker-compose.local.yml restart orator-bot
```

### Управление базами данных:
```bash
# Подключение к базе приложения
docker exec -it alex-orator-app-db-local psql -U alex_orator -d app_db

# Подключение к базе данных
docker exec -it alex-orator-data-db-local psql -U alex_orator -d data_db

# Резервное копирование
docker exec alex-orator-app-db-local pg_dump -U alex_orator app_db > backup_app.sql
docker exec alex-orator-data-db-local pg_dump -U alex_orator data_db > backup_data.sql
```

## 📊 Мониторинг

### Проверка статуса:
```bash
# Статус всех контейнеров
docker-compose -f docker-compose.local.yml ps

# Использование ресурсов
docker stats

# Проверка сетей
docker network ls
docker network inspect alex-orator-local-network
```

### Логи:
```bash
# Логи бота
docker-compose -f docker-compose.local.yml logs orator-bot

# Логи backend
docker-compose -f docker-compose.local.yml logs backend

# Логи баз данных
docker-compose -f docker-compose.local.yml logs app-db
docker-compose -f docker-compose.local.yml logs data-db
```

## 🔍 Отладка

### Подключение к контейнерам:
```bash
# Подключение к боту
docker exec -it alex-orator-bot-local bash

# Подключение к backend
docker exec -it alex-orator-backend-local bash

# Подключение к базе данных
docker exec -it alex-orator-app-db-local bash
```

### Проверка API:
```bash
# Проверка health endpoint
curl http://localhost:8000/health/

# Проверка документации API
open http://localhost:8000/docs
```

## 🛠️ Разработка

### Горячая перезагрузка:
- Backend автоматически перезагружается при изменении файлов
- Бот требует перезапуска контейнера для изменений

### Редактирование кода:
```bash
# Файлы монтируются в контейнеры
# Изменения в ./backend/ сразу отражаются в backend контейнере
# Изменения в ./telegram-bot/ требуют перезапуска orator-bot
```

### Тестирование:
```bash
# Запуск тестов бота
docker exec -it alex-orator-bot-local python test_orator_bot.py

# Запуск тестов backend
docker exec -it alex-orator-backend-local python -m pytest
```

## 🔒 Безопасность

### Переменные окружения:
- Никогда не коммитьте `.env` файл
- Используйте разные секреты для разных окружений
- Регулярно ротируйте JWT ключи

### Сети:
- Все сервисы изолированы в Docker сети
- Базы данных доступны только внутри сети
- Backend доступен на localhost:8000

## 📈 Масштабирование

### Для продакшена:
1. Создайте `docker-compose.prod.yml`
2. Настройте внешние базы данных
3. Добавьте reverse proxy (nginx)
4. Настройте SSL сертификаты
5. Добавьте мониторинг (Prometheus/Grafana)

### Пример prod конфигурации:
```yaml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend
      - orator-bot
```

## 🐛 Устранение неполадок

### Частые проблемы:

#### 1. Бот не запускается
```bash
# Проверьте токен
docker-compose -f docker-compose.local.yml logs orator-bot

# Проверьте подключение к backend
curl http://localhost:8000/health/
```

#### 2. Базы данных не подключаются
```bash
# Проверьте статус контейнеров
docker-compose -f docker-compose.local.yml ps

# Проверьте логи
docker-compose -f docker-compose.local.yml logs app-db
```

#### 3. Backend не отвечает
```bash
# Проверьте переменные окружения
docker exec -it alex-orator-backend-local env

# Проверьте подключение к БД
docker exec -it alex-orator-backend-local python -c "import asyncpg; print('DB OK')"
```

### Очистка:
```bash
# Полная очистка
docker-compose -f docker-compose.local.yml down -v
docker system prune -a
docker volume prune
```

## 📚 Дополнительные ресурсы

- [Docker Compose документация](https://docs.docker.com/compose/)
- [PostgreSQL в Docker](https://hub.docker.com/_/postgres)
- [FastAPI документация](https://fastapi.tiangolo.com/)
- [python-telegram-bot](https://python-telegram-bot.readthedocs.io/)

## 🤝 Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose -f docker-compose.local.yml logs`
2. Убедитесь, что все переменные окружения настроены
3. Проверьте, что порты не заняты другими сервисами
4. Создайте issue в репозитории с логами ошибок 