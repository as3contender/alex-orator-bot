.PHONY: help local-up local-down logs test clean build production-up production-down setup

# Переменные
COMPOSE_LOCAL = docker-compose -f docker-compose.local.yml
COMPOSE_PROD = docker-compose -f docker-compose.yml

help: ## Показать справку
	@echo "CloverdashBot Template - Команды управления"
	@echo ""
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Первоначальная настройка проекта
	@echo "🔧 Настройка CloverdashBot Template..."
	@mkdir -p logs
	@echo "📁 Создана директория logs/"
	@if [ ! -f .env ]; then \
		echo "📝 Создание .env файла..."; \
		cp backend/env_example.txt backend/.env; \
		cp telegram-bot/env_example.txt telegram-bot/.env; \
		echo "✅ Файлы .env созданы. Отредактируйте их перед запуском."; \
	else \
		echo "✅ Файл .env уже существует"; \
	fi
	@echo "🎉 Настройка завершена!"

local-up: ## Запуск локальной разработки
	@echo "🚀 Запуск локальной разработки..."
	$(COMPOSE_LOCAL) up -d
	@echo "✅ Сервисы запущены!"
	@echo "📊 Backend API: http://localhost:8000"
	@echo "📚 API Docs: http://localhost:8000/docs"
	@echo "🔍 Health Check: http://localhost:8000/health"

local-down: ## Остановка локальной разработки
	@echo "🛑 Остановка локальной разработки..."
	$(COMPOSE_LOCAL) down
	@echo "✅ Сервисы остановлены!"

local-restart: ## Перезапуск локальной разработки
	@echo "🔄 Перезапуск локальной разработки..."
	$(COMPOSE_LOCAL) restart
	@echo "✅ Сервисы перезапущены!"

production-up: ## Запуск production окружения
	@echo "🚀 Запуск production окружения..."
	$(COMPOSE_PROD) up -d
	@echo "✅ Production сервисы запущены!"

production-down: ## Остановка production окружения
	@echo "🛑 Остановка production окружения..."
	$(COMPOSE_PROD) down
	@echo "✅ Production сервисы остановлены!"

logs: ## Просмотр логов
	@echo "📋 Просмотр логов..."
	$(COMPOSE_LOCAL) logs -f

logs-backend: ## Просмотр логов backend
	@echo "📋 Логи Backend..."
	$(COMPOSE_LOCAL) logs -f backend

logs-telegram: ## Просмотр логов telegram бота
	@echo "📋 Логи Telegram Bot..."
	$(COMPOSE_LOCAL) logs -f telegram-bot

logs-db: ## Просмотр логов базы данных
	@echo "📋 Логи базы данных..."
	$(COMPOSE_LOCAL) logs -f app-db data-db

test: ## Запуск тестов
	@echo "🧪 Запуск тестов..."
	@cd backend && python -m pytest tests/ -v
	@cd telegram-bot && python -m pytest tests/ -v

test-backend: ## Запуск тестов backend
	@echo "🧪 Тесты Backend..."
	@cd backend && python -m pytest tests/ -v

test-telegram: ## Запуск тестов telegram бота
	@echo "🧪 Тесты Telegram Bot..."
	@cd telegram-bot && python -m pytest tests/ -v

build: ## Сборка Docker образов
	@echo "🔨 Сборка Docker образов..."
	docker build -t cloverdashbot-backend ./backend
	docker build -t cloverdashbot-telegram ./telegram-bot
	@echo "✅ Образы собраны!"

clean: ## Очистка контейнеров и образов
	@echo "🧹 Очистка..."
	$(COMPOSE_LOCAL) down -v
	$(COMPOSE_PROD) down -v
	docker system prune -f
	@echo "✅ Очистка завершена!"

clean-data: ## Очистка данных (ВНИМАНИЕ: удалит все данные!)
	@echo "⚠️  ВНИМАНИЕ: Это удалит все данные!"
	@read -p "Вы уверены? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	$(COMPOSE_LOCAL) down -v
	$(COMPOSE_PROD) down -v
	docker volume prune -f
	@echo "✅ Данные удалены!"

status: ## Статус сервисов
	@echo "📊 Статус сервисов..."
	$(COMPOSE_LOCAL) ps

health: ## Проверка здоровья сервисов
	@echo "🏥 Проверка здоровья сервисов..."
	@curl -s http://localhost:8000/health/ || echo "❌ Backend недоступен"
	@curl -s http://localhost:8000/health/info || echo "❌ Backend health info недоступен"

shell-backend: ## Shell в backend контейнер
	@echo "🐚 Shell в Backend..."
	$(COMPOSE_LOCAL) exec backend /bin/bash

shell-telegram: ## Shell в telegram контейнер
	@echo "🐚 Shell в Telegram Bot..."
	$(COMPOSE_LOCAL) exec telegram-bot /bin/bash

shell-db: ## Shell в базу данных
	@echo "🐚 Shell в базу данных..."
	$(COMPOSE_LOCAL) exec app-db psql -U cloverdashbot -d app_db

install-deps: ## Установка зависимостей для разработки
	@echo "📦 Установка зависимостей..."
	@cd backend && pip install -r requirements.txt
	@cd telegram-bot && pip install -r requirements.txt
	@echo "✅ Зависимости установлены!"

format: ## Форматирование кода
	@echo "🎨 Форматирование кода..."
	@cd backend && black . && isort .
	@cd telegram-bot && black . && isort .
	@echo "✅ Код отформатирован!"

lint: ## Проверка кода
	@echo "🔍 Проверка кода..."
	@cd backend && flake8 . && mypy .
	@cd telegram-bot && flake8 . && mypy .
	@echo "✅ Проверка завершена!"

docs: ## Генерация документации
	@echo "📚 Генерация документации..."
	@cd backend && pdoc --html --output-dir docs .
	@echo "✅ Документация сгенерирована!"

# Команды для быстрого доступа к API
api-docs: ## Открыть API документацию
	@echo "📚 Открытие API документации..."
	@open http://localhost:8000/docs || xdg-open http://localhost:8000/docs || echo "Откройте http://localhost:8000/docs в браузере"

api-health: ## Проверка API здоровья
	@echo "🏥 Проверка API здоровья..."
	@curl -s http://localhost:8000/health/ | jq . || curl -s http://localhost:8000/health/

# Команды для работы с базой данных
db-backup: ## Резервная копия базы данных
	@echo "💾 Создание резервной копии..."
	@mkdir -p backups
	$(COMPOSE_LOCAL) exec app-db pg_dump -U cloverdashbot app_db > backups/app_db_$(shell date +%Y%m%d_%H%M%S).sql
	$(COMPOSE_LOCAL) exec data-db pg_dump -U cloverdashbot data_db > backups/data_db_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Резервные копии созданы в директории backups/"

db-restore: ## Восстановление базы данных
	@echo "🔄 Восстановление базы данных..."
	@echo "⚠️  ВНИМАНИЕ: Это перезапишет текущие данные!"
	@read -p "Выберите файл для восстановления app_db: " app_file && \
	read -p "Выберите файл для восстановления data_db: " data_file && \
	$(COMPOSE_LOCAL) exec -T app-db psql -U cloverdashbot app_db < backups/$$app_file && \
	$(COMPOSE_LOCAL) exec -T data-db psql -U cloverdashbot data_db < backups/$$data_file
	@echo "✅ База данных восстановлена!" 