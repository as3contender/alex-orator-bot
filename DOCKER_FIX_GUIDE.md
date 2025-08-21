# Docker Fix Guide - Alex Orator Bot

## Общие проблемы и решения

### 1. Проблемы с подключением к базе данных

#### Ошибка: Connection refused
```bash
# Проверьте статус контейнера PostgreSQL
docker ps | grep postgres

# Если контейнер не запущен, запустите его
docker-compose up -d postgres

# Проверьте логи
docker-compose logs postgres
```

#### Ошибка: Authentication failed
```bash
# Проверьте переменные окружения
docker-compose exec postgres psql -U postgres -d postgres

# Создайте пользователя и базу данных
CREATE USER alex_orator WITH PASSWORD 'alex_orator_password';
CREATE DATABASE app_db OWNER alex_orator;
GRANT ALL PRIVILEGES ON DATABASE app_db TO alex_orator;
```

### 2. Проблемы с портами

#### Ошибка: Port already in use
```bash
# Найдите процесс, использующий порт
netstat -tulpn | grep :5432

# Остановите процесс или измените порт в docker-compose.yml
ports:
  - "5433:5432"  # Измените на свободный порт
```

### 3. Проблемы с правами доступа

#### Ошибка: Permission denied
```bash
# Измените права на директории
chmod -R 755 ./data
chown -R 1000:1000 ./data

# Или используйте sudo
sudo chown -R $USER:$USER ./data
```

## Пошаговое исправление

### Шаг 1: Остановка всех контейнеров
```bash
docker-compose down
docker system prune -f
```

### Шаг 2: Проверка конфигурации
```bash
# Проверьте docker-compose.yml
cat docker-compose.yml

# Проверьте переменные окружения
cat .env
```

### Шаг 3: Пересоздание контейнеров
```bash
# Удалите старые volumes
docker volume prune -f

# Запустите заново
docker-compose up -d --build
```

### Шаг 4: Проверка подключения
```bash
# Проверьте статус контейнеров
docker-compose ps

# Проверьте логи
docker-compose logs -f
```

## Частые проблемы

### 1. PostgreSQL не запускается
```bash
# Проверьте доступность порта
telnet localhost 5432

# Проверьте права на директорию данных
ls -la ./data/postgres

# Пересоздайте volume
docker volume rm alex-orator-bot_postgres_data
docker-compose up -d postgres
```

### 2. Redis не подключается
```bash
# Проверьте статус Redis
docker-compose exec redis redis-cli ping

# Если Redis не нужен, закомментируйте в docker-compose.yml
# redis:
#   image: redis:alpine
```

### 3. Проблемы с сетью
```bash
# Проверьте Docker сети
docker network ls

# Создайте новую сеть
docker network create alex-orator-network

# Обновите docker-compose.yml
networks:
  default:
    external:
      name: alex-orator-network
```

## Конфигурация для разработки

### docker-compose.local.yml
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: app_db
      POSTGRES_USER: alex_orator
      POSTGRES_PASSWORD: alex_orator_password
    ports:
      - "5434:5432"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    networks:
      - app-network

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
```

### Переменные окружения (.env)
```env
DB_HOST=localhost
DB_PORT=5434
DB_NAME=app_db
DB_USER=alex_orator
DB_PASSWORD=alex_orator_password
REDIS_URL=redis://localhost:6379
```

## Отладка

### Просмотр логов
```bash
# Все сервисы
docker-compose logs -f

# Конкретный сервис
docker-compose logs -f postgres

# Последние 100 строк
docker-compose logs --tail=100 postgres
```

### Вход в контейнер
```bash
# PostgreSQL
docker-compose exec postgres psql -U alex_orator -d app_db

# Redis
docker-compose exec redis redis-cli

# Bash в контейнере
docker-compose exec postgres bash
```

### Проверка состояния
```bash
# Статус контейнеров
docker-compose ps

# Использование ресурсов
docker stats

# Информация о контейнере
docker inspect alex-orator-bot_postgres_1
```

## Автоматическое исправление

### Скрипт fix_docker.sh
```bash
#!/bin/bash

echo "🔧 Исправление Docker проблем..."

# Остановка контейнеров
echo "Останавливаю контейнеры..."
docker-compose down

# Очистка
echo "Очищаю Docker..."
docker system prune -f
docker volume prune -f

# Пересоздание
echo "Пересоздаю контейнеры..."
docker-compose up -d --build

# Проверка
echo "Проверяю статус..."
sleep 10
docker-compose ps

echo "✅ Исправление завершено!"
```

### Запуск скрипта
```bash
chmod +x fix_docker.sh
./fix_docker.sh
```

## Полезные команды

### Мониторинг
```bash
# Следить за логами в реальном времени
docker-compose logs -f --tail=50

# Проверить использование диска
docker system df

# Очистить неиспользуемые ресурсы
docker system prune -a
```

### Резервное копирование
```bash
# Экспорт базы данных
docker-compose exec postgres pg_dump -U alex_orator app_db > backup.sql

# Импорт базы данных
docker-compose exec -T postgres psql -U alex_orator app_db < backup.sql
```

## Контакты

При возникновении проблем, которые не решаются данным руководством, обратитесь к администратору системы.
