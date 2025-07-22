#!/bin/bash

# Alex Orator Bot - Скрипт быстрого запуска
# Использование: ./start.sh [команда]
# Команды: start, stop, restart, logs, status, clean

set -e

COMPOSE_FILE="docker-compose.local.yml"
PROJECT_NAME="alex-orator"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Проверка наличия Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker не установлен. Установите Docker и попробуйте снова."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
        exit 1
    fi

    if ! docker info &> /dev/null; then
        error "Docker не запущен. Запустите Docker и попробуйте снова."
        exit 1
    fi
}

# Проверка наличия .env файла
check_env() {
    if [ ! -f ".env" ]; then
        warn "Файл .env не найден. Проверяю env.local..."
        if [ -f "env.local" ]; then
            cp env.local .env
            log "Файл .env создан из env.local"
        elif [ -f "env.example" ]; then
            cp env.example .env
            warn "Файл .env создан из env.example. Отредактируйте его перед запуском!"
            echo "Не забудьте установить BOT_TOKEN и другие переменные окружения."
            exit 1
        else
            error "Файлы env.local и env.example не найдены. Создайте .env файл вручную."
            exit 1
        fi
    fi
}

# Функция запуска
start() {
    log "Запуск Alex Orator Bot..."
    check_docker
    check_env
    
    info "Сборка и запуск контейнеров..."
    docker-compose -f $COMPOSE_FILE up -d --build
    
    log "Ожидание запуска сервисов..."
    sleep 10
    
    # Проверка статуса
    status
    
    log "Alex Orator Bot запущен!"
    info "Backend API: http://localhost:8000"
    info "API документация: http://localhost:8000/docs"
    info "Логи: ./start.sh logs"
}

# Функция остановки
stop() {
    log "Остановка Alex Orator Bot..."
    docker-compose -f $COMPOSE_FILE down
    log "Alex Orator Bot остановлен!"
}

# Функция перезапуска
restart() {
    log "Перезапуск Alex Orator Bot..."
    stop
    sleep 2
    start
}

# Функция просмотра логов
logs() {
    if [ -z "$2" ]; then
        log "Просмотр логов всех сервисов..."
        docker-compose -f $COMPOSE_FILE logs -f
    else
        log "Просмотр логов сервиса: $2"
        docker-compose -f $COMPOSE_FILE logs -f $2
    fi
}

# Функция проверки статуса
status() {
    log "Статус сервисов Alex Orator Bot:"
    echo ""
    docker-compose -f $COMPOSE_FILE ps
    echo ""
    
    # Проверка доступности API
    if curl -s http://localhost:8000/health/ > /dev/null; then
        log "✅ Backend API доступен"
    else
        warn "❌ Backend API недоступен"
    fi
    
    # Проверка баз данных
    if docker exec alex-orator-app-db-local pg_isready -U alex_orator > /dev/null 2>&1; then
        log "✅ База данных приложения доступна"
    else
        warn "❌ База данных приложения недоступна"
    fi
    
    if docker exec alex-orator-data-db-local pg_isready -U alex_orator > /dev/null 2>&1; then
        log "✅ База данных пользователей доступна"
    else
        warn "❌ База данных пользователей недоступна"
    fi
}

# Функция очистки
clean() {
    warn "Очистка всех данных Alex Orator Bot..."
    read -p "Вы уверены? Это удалит все данные! (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Остановка и удаление контейнеров..."
        docker-compose -f $COMPOSE_FILE down -v
        
        log "Удаление образов..."
        docker rmi $(docker images -q alex-orator-bot-local) 2>/dev/null || true
        docker rmi $(docker images -q alex-orator-backend-local) 2>/dev/null || true
        
        log "Очистка завершена!"
    else
        log "Очистка отменена."
    fi
}

# Функция помощи
help() {
    echo "Alex Orator Bot - Скрипт управления"
    echo ""
    echo "Использование: $0 [команда]"
    echo ""
    echo "Команды:"
    echo "  start     - Запуск всех сервисов"
    echo "  stop      - Остановка всех сервисов"
    echo "  restart   - Перезапуск всех сервисов"
    echo "  logs      - Просмотр логов всех сервисов"
    echo "  logs [сервис] - Просмотр логов конкретного сервиса"
    echo "  status    - Проверка статуса сервисов"
    echo "  clean     - Полная очистка (удаление данных)"
    echo "  help      - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0 start"
    echo "  $0 logs orator-bot"
    echo "  $0 status"
    echo ""
    echo "Сервисы:"
    echo "  app-db    - База данных приложения"
    echo "  data-db   - База данных пользователей"
    echo "  backend   - Backend API"
    echo "  orator-bot - Telegram бот"
}

# Основная логика
case "${1:-help}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs "$@"
        ;;
    status)
        status
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        help
        ;;
    *)
        error "Неизвестная команда: $1"
        echo ""
        help
        exit 1
        ;;
esac 