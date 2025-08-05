# 🚀 Быстрый деплой Alex Orator Bot

## 30-секундная инструкция

```bash
# 1. Подготовка конфигурации
cp deployment/deploy.env.example deployment/deploy.env
nano deployment/deploy.env  # Заполните REMOTE_HOST, SSH ключи, пароли

# 2. Создание .env для проекта
cp env.example .env
nano .env  # Заполните TELEGRAM_TOKEN, SECRET_KEY, пароли БД

# 3. Деплой
cd deployment
./deploy_alex_orator.sh
```

## ⚡ Минимальная конфигурация

### В `deployment/deploy.env`:
```bash
REMOTE_HOST=your-server.com
REMOTE_USER=ubuntu
SSH_KEY_PATH=~/.ssh/your-key
TELEGRAM_TOKEN=your_bot_token
APP_DB_PASSWORD=secure_password_123
DATA_DB_PASSWORD=secure_password_456
```

### В `.env` (корень проекта):
```bash
TELEGRAM_TOKEN=your_bot_token
APP_DB_PASSWORD=secure_password_123
DATA_DB_PASSWORD=secure_password_456
SECRET_KEY=generated_secret_key
JWT_SECRET_KEY=generated_jwt_secret
```

## 🎯 Результат

После успешного деплоя:
- ✅ Backend API: `http://your-server:8000`
- ✅ Swagger docs: `http://your-server:8000/docs`  
- ✅ Telegram Bot: работает и отвечает на /start
- ✅ 2 PostgreSQL БД на портах 5432, 5433

## 🛠️ Быстрые команды

```bash
# Только backend
./deploy_alex_orator.sh --backend-only

# Только bot
./deploy_alex_orator.sh --bot-only

# Без БД (использовать внешние)
./deploy_alex_orator.sh --no-db

# Логи
ssh user@server 'cd /opt/alex-orator-bot && docker-compose logs -f'

# Рестарт
ssh user@server 'cd /opt/alex-orator-bot && docker-compose restart'
```

## 🔐 Безопасность

**Обязательно смените в production:**
- `SECRET_KEY` (сгенерируйте новый)
- `JWT_SECRET_KEY` (сгенерируйте новый)
- `APP_DB_PASSWORD` (сложный пароль)
- `DATA_DB_PASSWORD` (сложный пароль)

```bash
# Генерация секретов
python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

---
📖 **Полная документация:** [README.md](README.md)