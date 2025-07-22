# 🔐 Настройка ключей и переменных окружения

## Обзор

Alex Orator Bot использует несколько типов ключей для безопасности:

- **JWT_SECRET_KEY** - для подписи JWT токенов
- **SECRET_KEY** - общий секретный ключ приложения
- **DB_PASSWORD** - пароль для баз данных PostgreSQL
- **BOT_TOKEN** - токен Telegram бота

## 🚀 Быстрая настройка

### 1. Генерация ключей

Запустите скрипт для автоматической генерации всех ключей:

```bash
python generate_keys.py
```

Этот скрипт:
- ✅ Генерирует криптографически безопасные ключи
- ✅ Создает файл `.env` с готовыми настройками
- ✅ Обновляет `docker-compose.local.yml`
- ✅ Проверяет безопасность ключей

### 2. Настройка Telegram бота

1. Получите токен у [@BotFather](https://t.me/BotFather)
2. Отредактируйте файл `.env`:
   ```bash
   BOT_TOKEN=your_actual_bot_token_here
   ```

### 3. Запуск системы

```bash
./start.sh start
```

## 🔧 Ручная настройка

### Генерация только ключей

Если нужно только сгенерировать ключи без создания .env:

```bash
python generate_keys_only.py
```

### Структура .env файла

```env
# Telegram Bot
BOT_TOKEN=your_telegram_bot_token_here

# Backend API
BACKEND_URL=http://localhost:8000
API_TIMEOUT=30
API_RETRY_ATTEMPTS=3
API_RETRY_DELAY=1

# Базы данных (для Docker)
APP_DATABASE_URL=postgresql://alex_orator:your_db_password@app-db:5432/app_db
DATA_DATABASE_URL=postgresql://alex_orator:your_db_password@data-db:5432/data_db
DB_PASSWORD=your_secure_password

# JWT и безопасность
JWT_SECRET_KEY=your_jwt_secret_key_here
SECRET_KEY=your_secret_key_here

# OpenAI (опционально)
OPENAI_API_KEY=your_openai_api_key_here

# Логирование
LOG_LEVEL=INFO
DEBUG=false

# Настройки бота
DEFAULT_LANGUAGE=ru
MAX_PAIRS_PER_USER=3
DEFAULT_MATCHING_LIMIT=5
```

## 🔒 Безопасность

### Требования к ключам

- **JWT_SECRET_KEY**: минимум 32 символа, рекомендуется 64+
- **SECRET_KEY**: минимум 32 байта (кодируется в base64)
- **DB_PASSWORD**: минимум 16 символов с разнообразием

### Рекомендации

1. **Никогда не коммитьте .env файл в git**
2. **Используйте разные ключи для разных окружений**
3. **Регулярно ротируйте ключи в продакшене**
4. **Храните резервные копии ключей в безопасном месте**

### Проверка безопасности

Скрипт `generate_keys.py` автоматически проверяет:
- ✅ Длину ключей
- ✅ Разнообразие символов
- ✅ Энтропию
- ✅ Криптографическую стойкость

## 🐳 Docker настройка

### Переменные окружения в Docker

Docker Compose автоматически загружает переменные из `.env` файла:

```yaml
environment:
  - JWT_SECRET_KEY=${JWT_SECRET_KEY}
  - SECRET_KEY=${SECRET_KEY}
  - DB_PASSWORD=${DB_PASSWORD}
```

### Обновление ключей в Docker

1. Обновите `.env` файл
2. Перезапустите контейнеры:
   ```bash
   ./start.sh restart
   ```

## 🔄 Ротация ключей

### Для разработки

```bash
# Генерация новых ключей
python generate_keys.py

# Перезапуск с новыми ключами
./start.sh restart
```

### Для продакшена

1. Сгенерируйте новые ключи
2. Обновите переменные окружения
3. Перезапустите сервисы
4. Убедитесь в работоспособности
5. Удалите старые ключи

## 🛠️ Устранение неполадок

### Ошибка "Invalid JWT token"

- Проверьте правильность `JWT_SECRET_KEY`
- Убедитесь, что ключ не изменился между перезапусками

### Ошибка подключения к базе данных

- Проверьте `DB_PASSWORD` в `.env`
- Убедитесь, что пароль совпадает в `docker-compose.local.yml`

### Ошибка "Bot token invalid"

- Проверьте правильность `BOT_TOKEN`
- Убедитесь, что бот не заблокирован

## 📝 Полезные команды

```bash
# Проверка статуса
./start.sh status

# Просмотр логов
./start.sh logs

# Очистка данных
./start.sh clean

# Генерация новых ключей
python generate_keys.py
```

## 🔗 Связанные файлы

- `generate_keys.py` - полная генерация с созданием .env
- `generate_keys_only.py` - генерация только ключей
- `docker-compose.local.yml` - конфигурация Docker
- `start.sh` - скрипт управления
- `.env` - переменные окружения (создается автоматически)
- `env.local` - шаблон для локальной разработки 