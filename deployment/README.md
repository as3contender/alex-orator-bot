# Alex Orator Bot - Deployment Guide

Автоматический деплой **Alex Orator Bot** на удаленный сервер с помощью Docker и docker-compose.

## 🚀 Быстрый старт

### 1. Подготовка конфигурации

```bash
# Скопируйте пример конфигурации
cp deployment/deploy.env.example deployment/deploy.env

# Отредактируйте конфигурацию
nano deployment/deploy.env
```

### 2. Запуск деплоя

```bash
# Перейдите в директорию deployment
cd deployment

# Сделайте скрипт исполняемым
chmod +x deploy_alex_orator.sh

# Запустите полный деплой
./deploy_alex_orator.sh
```

## 📋 Конфигурация

### Обязательные параметры в `deploy.env`:

```bash
# Сервер
REMOTE_HOST=your-server.com
REMOTE_USER=ubuntu
SSH_KEY_PATH=~/.ssh/your-key

# Безопасность
SECRET_KEY=your-generated-secret-key
JWT_SECRET_KEY=your-generated-jwt-secret
APP_DB_PASSWORD=secure_password
DATA_DB_PASSWORD=secure_password

# Telegram Bot
TELEGRAM_TOKEN=your_bot_token_from_botfather
```

### Генерация секретных ключей:

```bash
# Генерация SECRET_KEY
python3 -c "import secrets, base64; print('SECRET_KEY=' + base64.b64encode(secrets.token_bytes(32)).decode())"

# Генерация JWT_SECRET_KEY  
python3 -c "import secrets, base64; print('JWT_SECRET_KEY=' + base64.b64encode(secrets.token_bytes(32)).decode())"
```

## 🛠️ Варианты деплоя

### Полный деплой (все сервисы):
```bash
./deploy_alex_orator.sh
```

### Только backend API:
```bash
./deploy_alex_orator.sh --backend-only
```

### Только Telegram bot:
```bash
./deploy_alex_orator.sh --bot-only
```

### Без баз данных (использовать внешние):
```bash
./deploy_alex_orator.sh --no-db
```

### С кастомными параметрами:
```bash
./deploy_alex_orator.sh -h your-server.com -u ubuntu -k ~/.ssh/your-key
```

## 📊 Архитектура развертывания

Скрипт разворачивает следующие сервисы:

### 🗄️ Базы данных (если включены):
- **app-db**: PostgreSQL для приложения (порт 5432)
- **data-db**: PostgreSQL для пользовательских данных (порт 5433)

### 🔗 Backend API (если включен):
- **backend**: FastAPI сервер (порт 8000)
- Автоматические health checks
- Swagger документация на `/docs`

### 🤖 Telegram Bot (если включен):
- **telegram-bot**: Telegram бот
- Подключается к backend через внутреннюю сеть

### 🌐 Дополнительно:
- **nginx**: Reverse proxy (опционально, profile: production)
- **alex-orator-network**: Docker сеть для всех сервисов

## 🔧 Управление после деплоя

### Проверка статуса:
```bash
ssh user@server 'cd /opt/alex-orator-bot && docker-compose ps'
```

### Просмотр логов:
```bash
# Все сервисы
ssh user@server 'cd /opt/alex-orator-bot && docker-compose logs -f'

# Только backend
ssh user@server 'cd /opt/alex-orator-bot && docker-compose logs -f backend'

# Только bot
ssh user@server 'cd /opt/alex-orator-bot && docker-compose logs -f telegram-bot'
```

### Перезапуск:
```bash
ssh user@server 'cd /opt/alex-orator-bot && docker-compose restart'
```

### Остановка:
```bash
ssh user@server 'cd /opt/alex-orator-bot && docker-compose down'
```

### Обновление:
```bash
# Повторно запустите скрипт деплоя
./deploy_alex_orator.sh
```

## 🔐 Требования к серверу

### Минимальные системные требования:
- **OS**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **RAM**: 2GB минимум, 4GB рекомендуется
- **Disk**: 10GB свободного места
- **Network**: Открытые порты 8000 (API), 5432, 5433 (БД)

### Автоматически устанавливается:
- Docker
- docker-compose
- Все необходимые зависимости

### SSH доступ:
- Пользователь должен иметь права sudo
- SSH ключ или пароль для подключения
- Для не-root пользователей: добавление в группу docker

## 📁 Структура файлов на сервере

```
/opt/alex-orator-bot/
├── docker-compose.yml          # Конфигурация сервисов
├── .env                        # Переменные окружения
├── backend/                    # Backend API код
├── telegram-bot/              # Telegram bot код
├── deployment/                # SQL инициализация
└── logs/                      # Логи приложений
```

## 🔍 Диагностика проблем

### Backend не стартует:
```bash
# Проверить логи
ssh user@server 'cd /opt/alex-orator-bot && docker-compose logs backend'

# Проверить health endpoint
curl http://your-server:8000/health/
```

### Bot не отвечает:
```bash
# Проверить логи
ssh user@server 'cd /opt/alex-orator-bot && docker-compose logs telegram-bot'

# Проверить токен в .env файле
```

### Проблемы с БД:
```bash
# Проверить статус контейнеров
ssh user@server 'cd /opt/alex-orator-bot && docker-compose ps'

# Подключиться к БД
ssh user@server 'docker exec -it alex-orator-bot-app-db psql -U alex_orator -d app_db'
```

## 🚨 Безопасность

### Обязательно измените в production:
- [ ] `SECRET_KEY` - новый уникальный ключ
- [ ] `JWT_SECRET_KEY` - новый уникальный ключ  
- [ ] `APP_DB_PASSWORD` - сильный пароль
- [ ] `DATA_DB_PASSWORD` - сильный пароль
- [ ] `TELEGRAM_TOKEN` - ваш реальный токен от @BotFather

### Рекомендации:
- Используйте SSH ключи вместо паролей
- Настройте firewall на сервере
- Регулярно обновляйте зависимости
- Делайте бэкапы баз данных

## 📞 Поддержка

При проблемах с деплоем:

1. **Проверьте логи** с помощью команд выше
2. **Убедитесь в корректности** конфигурации в `deploy.env`
3. **Проверьте доступность сервера** и SSH подключение
4. **Убедитесь в наличии свободного места** на диске

## 🎯 Готовые конфигурации

### Для продакшена:
```bash
DEPLOY_BACKEND=true
DEPLOY_BOT=true
DEPLOY_DATABASES=true
DEBUG=false
LOG_LEVEL=INFO
```

### Для разработки/тестирования:
```bash
DEPLOY_BACKEND=true
DEPLOY_BOT=false
DEPLOY_DATABASES=true
DEBUG=true
LOG_LEVEL=DEBUG
```

---

**Alex Orator Bot** готов к продакшену! 🎉