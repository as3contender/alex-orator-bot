# 🚀 Деплой админ-панели

## Обзор

Этот документ описывает процесс деплоя админ-панели Alex Orator Bot на продакшен сервер.

## ⚠️ Безопасность

**Админ-панель по умолчанию отключена в деплое для безопасности!**

- Админ-панель предоставляет полный доступ к управлению системой
- Рекомендуется развертывать только на защищенных серверах
- Обязательно настройте HTTPS и ограничьте доступ по IP

## 🔧 Настройка деплоя

### 1. Включение админ-панели

Отредактируйте файл `deployment/deploy.env`:

```bash
# Включить деплой админ-панели
DEPLOY_ADMIN_PANEL=true
```

### 2. Проверка переменных окружения

Убедитесь, что в `deploy.env` настроены все необходимые переменные:

```bash
# Database
APP_DB_PASSWORD=your-super-secure-database-password

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-minimum-32-characters
SECRET_KEY=your-super-secret-key

# Telegram Bot
TELEGRAM_TOKEN=your-telegram-bot-token
```

## 🚀 Процесс деплоя

### Полный деплой с админ-панелью

```bash
# 1. Включите админ-панель в deploy.env
echo "DEPLOY_ADMIN_PANEL=true" >> deployment/deploy.env

# 2. Запустите деплой
./deployment/deploy_alex_orator.sh
```

### Деплой только админ-панели

```bash
# Настройте deploy.env для деплоя только админ-панели
cat > deployment/deploy.env << EOF
REMOTE_HOST=your-server.com
REMOTE_USER=ubuntu
SSH_KEY_PATH=~/.ssh/your-ssh-key
REMOTE_DEPLOY_DIR=/opt/alex-orator-bot

DEPLOY_DATABASES=false
DEPLOY_BACKEND=false
DEPLOY_BOT=false
DEPLOY_WORKER=false
DEPLOY_ADMIN_PANEL=true

APP_DB_PASSWORD=your-db-password
JWT_SECRET_KEY=your-jwt-secret
SECRET_KEY=your-secret-key
TELEGRAM_TOKEN=your-bot-token
EOF

# Запустите деплой
./deployment/deploy_alex_orator.sh
```

## 🔍 Проверка деплоя

### Проверка статуса сервисов

```bash
# Проверка статуса всех сервисов
ssh user@server "cd /opt/alex-orator-bot && docker-compose ps"

# Проверка статуса только админ-панели
ssh user@server "cd /opt/alex-orator-bot && docker-compose ps admin-panel"
```

### Проверка логов

```bash
# Просмотр логов админ-панели
ssh user@server "cd /opt/alex-orator-bot && docker-compose logs -f admin-panel"

# Проверка ошибок
ssh user@server "cd /opt/alex-orator-bot && docker-compose logs admin-panel | grep -i error"
```

### Проверка доступности

```bash
# Проверка порта
ssh user@server "curl -I http://localhost:8501"

# Проверка извне (если порт открыт)
curl -I http://your-server.com:8501
```

## 🔑 Создание администратора

После успешного деплоя создайте администратора:

```bash
# Вход на сервер
ssh user@server

# Вход в контейнер админ-панели
cd /opt/alex-orator-bot
docker-compose exec admin-panel bash

# Создание администратора
python utils/migrate_passwords.py --create-admin
```

Или с указанным паролем:

```bash
python utils/migrate_passwords.py --admin-password "YourSecurePassword123!"
```

## 🌐 Настройка доступа

### Базовый доступ

По умолчанию админ-панель доступна на порту 8501:

- **URL**: http://your-server.com:8501
- **Логин**: `admin`
- **Пароль**: (создается при первом запуске)

### Рекомендуемая настройка с nginx

Создайте конфигурацию nginx для безопасного доступа:

```nginx
server {
    listen 443 ssl;
    server_name admin.your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Ограничение доступа по IP (опционально)
    allow 192.168.1.0/24;
    allow 10.0.0.0/8;
    deny all;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🔄 Обновление

### Обновление админ-панели

```bash
# Остановка сервиса
ssh user@server "cd /opt/alex-orator-bot && docker-compose stop admin-panel"

# Пересборка и запуск
ssh user@server "cd /opt/alex-orator-bot && docker-compose up -d --build admin-panel"
```

### Полное обновление

```bash
# Пересборка всех сервисов
./deployment/deploy_alex_orator.sh
```

## 🐛 Устранение неполадок

### Проблемы с подключением к БД

```bash
# Проверка переменных окружения
ssh user@server "cd /opt/alex-orator-bot && docker-compose exec admin-panel env | grep DB"

# Проверка доступности БД
ssh user@server "cd /opt/alex-orator-bot && docker-compose exec admin-panel ping app-db"
```

### Проблемы с импортами

```bash
# Тест импортов
ssh user@server "cd /opt/alex-orator-bot && docker-compose exec admin-panel python test_imports.py"
```

### Проблемы с аутентификацией

```bash
# Проверка пользователей в БД
ssh user@server "cd /opt/alex-orator-bot && docker-compose exec admin-panel python -c \"
from database.database import AdminDatabase
db = AdminDatabase()
db.connect()
cursor = db.conn.cursor()
cursor.execute('SELECT username, telegram_id FROM users WHERE telegram_id IS NULL')
print(cursor.fetchall())
\""
```

### Проблемы с портами

```bash
# Проверка занятых портов
ssh user@server "netstat -tlnp | grep 8501"

# Проверка firewall
ssh user@server "sudo ufw status"
```

## 📊 Мониторинг

### Логирование

```bash
# Просмотр логов в реальном времени
ssh user@server "cd /opt/alex-orator-bot && docker-compose logs -f admin-panel"

# Поиск ошибок
ssh user@server "cd /opt/alex-orator-bot && docker-compose logs admin-panel | grep -i error"
```

### Метрики

```bash
# Использование ресурсов
ssh user@server "docker stats alex-orator-bot-admin-panel"

# Проверка здоровья
ssh user@server "curl -f http://localhost:8501/_stcore/health"
```

## 🔒 Рекомендации по безопасности

1. **HTTPS**: Обязательно используйте SSL сертификат
2. **Firewall**: Ограничьте доступ по IP адресам
3. **VPN**: Используйте VPN для доступа к админ-панели
4. **Мониторинг**: Настройте логирование и мониторинг
5. **Backup**: Регулярно создавайте резервные копии БД
6. **Обновления**: Регулярно обновляйте зависимости
7. **Пароли**: Используйте сложные пароли и регулярно их меняйте

## 📚 Полезные команды

```bash
# Перезапуск админ-панели
ssh user@server "cd /opt/alex-orator-bot && docker-compose restart admin-panel"

# Просмотр ресурсов
ssh user@server "docker stats"

# Очистка неиспользуемых образов
ssh user@server "docker system prune -f"

# Создание резервной копии БД
ssh user@server "cd /opt/alex-orator-bot && docker-compose exec app-db pg_dump -U alex_orator app_db > backup.sql"
```

---

**Статус:** ✅ Готов к продакшену
