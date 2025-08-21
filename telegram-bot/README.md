# CloverdashBot Telegram

Telegram бот для интеллектуального анализа данных с использованием LLM.

## 🚀 Быстрый старт

### Локальная разработка
```bash
# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp env_example.txt .env
# Отредактировать .env файл

# Запуск
python bot.py
```

### Docker
```bash
# Сборка образа
docker build -t cloverdashbot-telegram .

# Запуск контейнера
docker run --env-file .env cloverdashbot-telegram
```

## 📋 Доступные команды

### Основные команды
- `/start` - Начало работы с ботом
- `/help` - Справка по использованию
- `/tables` - Список доступных таблиц
- `/sample` - Примеры данных из таблиц
- `/settings` - Настройки пользователя

### Быстрые команды
- `/en` - Переключить интерфейс на английский
- `/ru` - Переключить интерфейс на русский

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Описание | Обязательная |
|------------|----------|--------------|
| `TELEGRAM_TOKEN` | Токен бота от @BotFather | Да |
| `BACKEND_URL` | URL backend API | Да |
| `LOG_LEVEL` | Уровень логирования | Нет |

### Получение токена бота

1. Найдите @BotFather в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен в `.env` файл

## 🗂️ Структура проекта

```
telegram-bot/
├── bot.py                 # Основной файл бота
├── config.py              # Конфигурация
├── models.py              # Модели данных
├── exceptions.py          # Кастомные исключения
├── api_client.py          # HTTP клиент для Backend
├── handlers.py            # Обработчики команд
├── query_handler.py       # Обработчик запросов
├── error_handler.py       # Обработчик ошибок
├── formatters.py          # Форматирование сообщений
├── translations.py        # Система переводов
├── requirements.txt       # Зависимости
├── Dockerfile            # Docker образ
└── env_example.txt       # Пример конфигурации
```

## 🔒 Безопасность

- Аутентификация через Telegram ID
- JWT токены для API запросов
- Валидация всех входных данных
- Обработка ошибок без утечки информации

## 📊 Возможности

### Анализ данных
- Запросы на естественном языке
- Автоматическая генерация SQL
- Форматированные результаты в таблицах
- Объяснения SQL запросов

### Настройки пользователя
- Выбор языка интерфейса (RU/EN)
- Включение/отключение объяснений
- Включение/отключение показа SQL
- Настройка максимального количества результатов

### Интерактивность
- Инлайн-кнопки для примеров
- Быстрая смена языка
- Управление настройками через кнопки
- Выбор таблиц для просмотра данных

## 🧪 Тестирование

```bash
# Запуск тестов
python -m pytest tests/

# Запуск с coverage
python -m pytest --cov=. tests/
```

## 📝 Логирование

Бот использует структурированное логирование через Loguru. Логи сохраняются в файл `logs/telegram-bot.log` с ротацией.

## 🔄 Интеграция с Backend

Бот взаимодействует с Backend API для:
- Аутентификации пользователей
- Выполнения запросов к базе данных
- Получения схемы базы данных
- Управления настройками пользователей

## 🚀 Развертывание

### Docker Compose
```yaml
version: '3.8'
services:
  telegram-bot:
    build: ./telegram-bot
    environment:
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
      - BACKEND_URL=http://backend:8000
    depends_on:
      - backend
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cloverdashbot-telegram
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cloverdashbot-telegram
  template:
    metadata:
      labels:
        app: cloverdashbot-telegram
    spec:
      containers:
      - name: telegram-bot
        image: cloverdashbot-telegram:latest
        env:
        - name: TELEGRAM_TOKEN
          valueFrom:
            secretKeyRef:
              name: telegram-secret
              key: token
        - name: BACKEND_URL
          value: "http://backend-service:8000"
```

## 🐛 Отладка

### Проверка подключения к Backend
```bash
curl http://localhost:8000/health/
```

### Просмотр логов
```bash
tail -f logs/telegram-bot.log
```

### Тестирование бота
1. Найдите вашего бота в Telegram
2. Отправьте команду `/start`
3. Проверьте работу всех команд
4. Протестируйте запросы на естественном языке 