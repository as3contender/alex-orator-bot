# 🐳 Настройка Docker для админ-панели

## Обзор

Админ-панель может быть запущена в Docker контейнере для изоляции и упрощения развертывания.

## 📋 Требования

- Docker и Docker Compose
- Доступ к базе данных PostgreSQL
- Переменные окружения настроены

## 🚀 Быстрый старт

### 1. Запуск только админ-панели

```bash
# Из корня проекта
docker-compose -f docker-compose.local.yml up admin-panel

# Или используя скрипт
cd admin-panel
./run_docker.sh
```

### 2. Запуск всей системы

```bash
# Из корня проекта
docker-compose -f docker-compose.local.yml up
```

## 🔧 Конфигурация

### Переменные окружения

Админ-панель использует следующие переменные окружения:

```yaml
# Database Configuration
DB_HOST: app-db                    # Хост базы данных
DB_PORT: 5432                      # Порт базы данных
DB_NAME: app_db                    # Имя базы данных
DB_USER: alex_orator               # Пользователь БД
APP_DB_PASSWORD: secure_password   # Пароль БД

# Security Configuration
JWT_SECRET_KEY: dev-jwt-secret     # Секретный ключ JWT

# Security Settings
MAX_LOGIN_ATTEMPTS: 5              # Максимум попыток входа
LOGIN_TIMEOUT_MINUTES: 15          # Таймаут блокировки
SESSION_TIMEOUT_MINUTES: 30        # Таймаут сессии
BCRYPT_ROUNDS: 12                  # Раунды bcrypt

# Streamlit Configuration
STREAMLIT_SERVER_PORT: 8501        # Порт Streamlit
STREAMLIT_SERVER_ADDRESS: 0.0.0.0  # Адрес привязки
STREAMLIT_SERVER_HEADLESS: true    # Безголовый режим
STREAMLIT_SERVER_ENABLE_CORS: false # Отключить CORS
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION: true # Защита XSRF

# Logging
LOG_LEVEL: INFO                    # Уровень логирования
```

### Порты

- **8501** - Админ-панель (Streamlit)

## 🏗️ Структура Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc g++ libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY config/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание пользователя
RUN useradd -m -u 1000 streamlit && \
    chown -R streamlit:streamlit /app
USER streamlit

EXPOSE 8501

CMD ["streamlit", "run", "ui/admin_app.py"]
```

### Docker Compose сервис

```yaml
admin-panel:
  build: 
    context: ./admin-panel
    dockerfile: Dockerfile
  container_name: alex-orator-admin-panel-local
  environment:
    - DB_HOST=app-db
    - DB_PORT=5432
    - DB_NAME=app_db
    - DB_USER=alex_orator
    - APP_DB_PASSWORD=${APP_DATABASE_PASSWORD:-secure_password}
    - JWT_SECRET_KEY=${JWT_SECRET_KEY:-dev-jwt-secret}
    # ... другие переменные
  ports:
    - "8501:8501"
  depends_on:
    - app-db
    - backend
  networks:
    - alex-orator-local-network
  restart: unless-stopped
  volumes:
    - ./admin-panel:/app
    - ./logs:/app/logs
```

## 🔍 Отладка

### Просмотр логов

```bash
# Логи админ-панели
docker-compose -f docker-compose.local.yml logs admin-panel

# Логи в реальном времени
docker-compose -f docker-compose.local.yml logs -f admin-panel
```

### Вход в контейнер

```bash
# Вход в контейнер админ-панели
docker-compose -f docker-compose.local.yml exec admin-panel bash

# Проверка переменных окружения
docker-compose -f docker-compose.local.yml exec admin-panel env
```

### Проверка подключения к БД

```bash
# Вход в контейнер
docker-compose -f docker-compose.local.yml exec admin-panel bash

# Тест подключения
python -c "from database.database import AdminDatabase; db = AdminDatabase(); db.connect(); print('✅ Подключение к БД успешно')"
```

### Проверка импортов

```bash
# Вход в контейнер
docker-compose -f docker-compose.local.yml exec admin-panel bash

# Тест импортов
python test_imports.py
```

## 🛠️ Разработка

### Горячая перезагрузка

При разработке код автоматически перезагружается благодаря volume mount:

```yaml
volumes:
  - ./admin-panel:/app
```

### Отладка

Для отладки можно запустить с дополнительными флагами:

```bash
docker-compose -f docker-compose.local.yml run --rm admin-panel streamlit run ui/admin_app.py --logger.level=debug
```

## 🔒 Безопасность

### Рекомендации для продакшена

1. **Создайте администратора вручную**
2. **Используйте сильные секретные ключи**
3. **Настройте HTTPS**
4. **Ограничьте доступ по IP**
5. **Регулярно обновляйте образы**

### Переменные для продакшена

```bash
# Создайте .env файл с сильными значениями
JWT_SECRET_KEY=your-super-secret-jwt-key-here
APP_DATABASE_PASSWORD=your-secure-database-password
```

⚠️ **ВАЖНО:** 
- Используйте сильные, уникальные пароли (минимум 16 символов)
- JWT_SECRET_KEY должен быть случайной строкой (минимум 32 символа)
- Никогда не коммитьте реальные пароли в Git!

## 🐛 Устранение неполадок

### Проблемы с подключением к БД

1. **Проверьте, что БД запущена:**
   ```bash
   docker-compose -f docker-compose.local.yml ps app-db
   ```

2. **Проверьте переменные окружения:**
   ```bash
   docker-compose -f docker-compose.local.yml exec admin-panel env | grep DB
   ```

3. **Проверьте сеть:**
   ```bash
   docker-compose -f docker-compose.local.yml exec admin-panel ping app-db
   ```

### Проблемы с портами

1. **Проверьте, что порт 8501 свободен:**
   ```bash
   lsof -i :8501
   ```

2. **Измените порт при необходимости:**
   ```yaml
   ports:
     - "8502:8501"  # Внешний порт 8502
   ```

### Проблемы с правами доступа

1. **Проверьте права на файлы:**
   ```bash
   ls -la admin-panel/
   ```

2. **Исправьте права при необходимости:**
   ```bash
   chmod -R 755 admin-panel/
   ```

## 📚 Полезные команды

```bash
# Сборка образа
docker-compose -f docker-compose.local.yml build admin-panel

# Запуск в фоне
docker-compose -f docker-compose.local.yml up -d admin-panel

# Остановка
docker-compose -f docker-compose.local.yml stop admin-panel

# Удаление контейнера
docker-compose -f docker-compose.local.yml rm admin-panel

# Пересборка и запуск
docker-compose -f docker-compose.local.yml up --build admin-panel
```

---

**Статус:** ✅ Готов к использованию
