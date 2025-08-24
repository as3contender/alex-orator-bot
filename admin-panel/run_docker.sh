#!/bin/bash

# Скрипт для запуска админ-панели в Docker

echo "🚀 Запуск админ-панели в Docker..."

# Проверяем, что мы в корне проекта
if [ ! -f "../docker-compose.local.yml" ]; then
    echo "❌ Ошибка: Запустите скрипт из корня проекта (alex-orator-bot/)"
    exit 1
fi

# Переходим в корень проекта
cd ..

# Проверяем, что Docker запущен
if ! docker info > /dev/null 2>&1; then
    echo "❌ Ошибка: Docker не запущен"
    exit 1
fi

# Собираем и запускаем только админ-панель
echo "🔨 Сборка админ-панели..."
docker-compose -f docker-compose.local.yml build admin-panel

if [ $? -ne 0 ]; then
    echo "❌ Ошибка сборки админ-панели"
    exit 1
fi

echo "🚀 Запуск админ-панели..."
docker-compose -f docker-compose.local.yml up admin-panel

echo "✅ Админ-панель запущена!"
echo "🌐 Откройте браузер: http://localhost:8501"
echo "⚠️  Создайте администратора вручную:"
echo "   docker-compose -f docker-compose.local.yml exec admin-panel python utils/migrate_passwords.py"
