#!/bin/bash

# Скрипт для импорта данных из локальной базы в удаленную
# Использование: ./import_data_to_remote.sh

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Начинаем импорт данных в удаленную базу...${NC}"

# Загружаем переменные окружения
if [ -f "deploy.env" ]; then
    source deploy.env
else
    echo -e "${RED}❌ Файл deploy.env не найден!${NC}"
    exit 1
fi

# Проверяем наличие файла с данными
if [ ! -f "local_data_export.sql" ]; then
    echo -e "${RED}❌ Файл local_data_export.sql не найден!${NC}"
    echo -e "${YELLOW}💡 Сначала выполните экспорт данных из локальной базы${NC}"
    exit 1
fi

echo -e "${GREEN}📤 Копируем файл с данными на удаленный сервер...${NC}"

# Копируем файл с данными на удаленный сервер
scp -i "$SSH_KEY_PATH" local_data_export.sql "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DEPLOY_DIR/"

echo -e "${GREEN}✅ Файл скопирован на сервер${NC}"

echo -e "${GREEN}🗄️ Импортируем данные в удаленную базу...${NC}"

# Подключаемся к удаленному серверу и импортируем данные
ssh -i "$SSH_KEY_PATH" "$REMOTE_USER@$REMOTE_HOST" << 'EOF'
    cd /opt/alex-orator-bot
    
    echo "🔄 Останавливаем контейнеры для безопасного импорта..."
    docker-compose down
    
    echo "🗄️ Импортируем данные в базу..."
    docker-compose up -d app-db
    
    # Ждем, пока база данных запустится
    echo "⏳ Ждем запуска базы данных..."
    sleep 10
    
    # Импортируем данные
    echo "📥 Импортируем bot_content и topics..."
    docker exec alex-orator-bot-app-db psql -U alex_orator -d app_db -c "DELETE FROM bot_content;"
    docker exec alex-orator-bot-app-db psql -U alex_orator -d app_db -c "DELETE FROM topics;"
    docker exec -i alex-orator-bot-app-db psql -U alex_orator -d app_db < local_data_export.sql
    
    echo "✅ Данные импортированы"
    
    echo "🚀 Запускаем все сервисы..."
    docker-compose up -d
    
    echo "⏳ Ждем запуска сервисов..."
    sleep 15
    
    echo "📊 Проверяем статус сервисов..."
    docker-compose ps
    
    echo "🧹 Очищаем временные файлы..."
    rm -f local_data_export.sql
EOF

echo -e "${GREEN}✅ Импорт данных завершен!${NC}"
echo -e "${YELLOW}💡 Проверьте логи сервисов:${NC}"
echo -e "${YELLOW}   docker-compose logs backend${NC}"
echo -e "${YELLOW}   docker-compose logs telegram-bot${NC}" 