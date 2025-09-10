# 🚀 Развертывание админ-панели в продакшене

## Обзор

Этот документ описывает процесс развертывания админ-панели Alex Orator Bot в продакшен среде.

## 📋 Требования

- Docker и Docker Compose
- PostgreSQL база данных
- Переменные окружения настроены
- SSL сертификат (рекомендуется)

## 🔧 Настройка

### 1. Переменные окружения

Создайте файл `.env` в корне проекта с необходимыми переменными:

```bash
# Database
APP_DB_PASSWORD=your-super-secure-database-password

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-minimum-32-characters
SECRET_KEY=your-super-secret-key

# Telegram Bot
BOT_TOKEN=your-telegram-bot-token
```

### 2. Настройка базы данных

Убедитесь, что база данных PostgreSQL настроена и доступна:

```bash
# Проверьте подключение к БД
docker-compose exec app-db psql -U alex_orator -d app_db -c "SELECT version();"
```

### 3. Применение изменений в БД

```bash
# Примените изменения для поддержки системных администраторов
docker-compose exec admin-panel python utils/apply_db_changes.py
```

## 🚀 Развертывание

### Полное развертывание

```bash
# Сборка и запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps
```

### Только админ-панель

```bash
# Сборка и запуск только админ-панели
docker-compose up -d admin-panel

# Проверка логов
docker-compose logs -f admin-panel
```

## 🔑 Создание администратора

После развертывания создайте администратора:

```bash
# Вход в контейнер админ-панели
docker-compose exec admin-panel bash

# Создание администратора
python utils/migrate_passwords.py --create-admin
```

Или с указанным паролем:

```bash
python utils/migrate_passwords.py --admin-password "YourSecurePassword123!"
```

## 🌐 Доступ

- **URL:** http://your-domain:8501
- **Порт:** 8501

## 🔒 Безопасность

### Рекомендации для продакшена

1. **HTTPS**: Настройте reverse proxy (nginx) с SSL сертификатом
2. **Firewall**: Ограничьте доступ по IP адресам
3. **VPN**: Используйте VPN для доступа к админ-панели
4. **Мониторинг**: Настройте логирование и мониторинг
5. **Backup**: Регулярно создавайте резервные копии БД

### Пример nginx конфигурации

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📊 Мониторинг

### Логи

```bash
# Просмотр логов админ-панели
docker-compose logs -f admin-panel

# Просмотр логов всех сервисов
docker-compose logs -f
```

### Проверка здоровья

```bash
# Проверка статуса контейнеров
docker-compose ps

# Проверка подключения к БД
docker-compose exec admin-panel python -c "
from database.database import AdminDatabase
db = AdminDatabase()
db.connect()
print('✅ Подключение к БД успешно')
"
```

## 🔄 Обновления

### Обновление админ-панели

```bash
# Остановка сервиса
docker-compose stop admin-panel

# Пересборка образа
docker-compose build admin-panel

# Запуск с новой версией
docker-compose up -d admin-panel
```

### Обновление всех сервисов

```bash
# Остановка всех сервисов
docker-compose down

# Пересборка всех образов
docker-compose build

# Запуск всех сервисов
docker-compose up -d
```

## 🐛 Устранение неполадок

### Проблемы с подключением к БД

```bash
# Проверка переменных окружения
docker-compose exec admin-panel env | grep DB

# Проверка доступности БД
docker-compose exec admin-panel ping app-db
```

### Проблемы с импортами

```bash
# Тест импортов
docker-compose exec admin-panel python test_imports.py
```

### Проблемы с аутентификацией

```bash
# Проверка пользователей в БД
docker-compose exec admin-panel python -c "
from database.database import AdminDatabase
db = AdminDatabase()
db.connect()
cursor = db.conn.cursor()
cursor.execute('SELECT username, telegram_id FROM users WHERE telegram_id IS NULL')
print(cursor.fetchall())
"
```

## 📚 Полезные команды

```bash
# Перезапуск админ-панели
docker-compose restart admin-panel

# Просмотр ресурсов
docker stats

# Очистка неиспользуемых образов
docker system prune -f

# Создание резервной копии БД
docker-compose exec app-db pg_dump -U alex_orator app_db > backup.sql
```

---

**Статус:** ✅ Готов к продакшену
