# 🎯 План реализации "Alex Orator Bot"

## 📋 Описание проекта
Бот для подбора пар для тренировки ораторского искусства. Пользователи регистрируются на неделю, выбирают темы и время, получают 3 кандидата для выбора пары.

## 🏗️ Архитектура
- **Telegram Bot** ↔ **FastAPI Backend** ↔ **PostgreSQL**
- Основан на шаблоне CloverdashBot Template
- Разделение системных и пользовательских данных

## 📋 Этап 1: Анализ и подготовка архитектуры

### 1.1 Модификация структуры базы данных
**Application Database** (новые таблицы):
```sql
-- Пользователи и их профили
users (расширить существующую)
  - telegram_id, username, first_name, last_name
  - registration_date, total_sessions, gender
  - feedback_count, is_active

-- Регистрации на недели
week_registrations
  - id, user_id, week_start_date, week_end_date
  - preferred_time_msk, status (active/cancelled)
  - created_at, cancelled_at

-- Выбранные темы пользователей
user_topics
  - id, user_id, week_registration_id
  - topic_path (например: "Подача - Темы речи уровень 1")
  - created_at

-- Пары пользователей
user_pairs
  - id, user1_id, user2_id, week_registration_id
  - status (pending/confirmed/cancelled)
  - created_at, confirmed_at, cancelled_at

-- Обратная связь
session_feedback
  - id, pair_id, from_user_id, to_user_id
  - feedback_text, rating (1-5)
  - created_at

-- Тексты и контент
bot_content
  - id, content_key (welcome_message, topic_tree, etc.)
  - content_text (markdown), language (ru/en)
  - is_active, created_at, updated_at
```

### 1.2 Структура тем (дерево)
```json
{
  "topics": [
    {
      "id": "delivery",
      "name": "Подача",
      "children": [
        {
          "id": "speech_topics_l1", 
          "name": "Темы речи уровень 1",
          "description": "Базовые техники работы с темами"
        }
      ]
    }
  ]
}
```

## 📋 Этап 2: Backend API разработка

### 2.1 Новые API эндпоинты
```python
# Пользователи
POST /api/users/register          # Регистрация пользователя
GET  /api/users/profile           # Получить профиль
PUT  /api/users/profile           # Обновить профиль

# Регистрации на недели
POST /api/weeks/register          # Зарегистрироваться на неделю
DELETE /api/weeks/register        # Отменить регистрацию
GET  /api/weeks/current           # Текущая неделя
GET  /api/weeks/next              # Следующая неделя

# Темы
GET  /api/topics/tree             # Дерево тем
POST /api/users/topics            # Выбрать темы

# Пары
POST /api/pairs/match             # Подобрать пары
POST /api/pairs/confirm           # Подтвердить пару
GET  /api/pairs/my                # Мои пары
DELETE /api/pairs/cancel          # Отменить пару

# Обратная связь
POST /api/feedback/submit         # Оставить обратную связь
GET  /api/feedback/history        # История обратной связи

# Контент
GET  /api/content/{key}           # Получить контент по ключу
```

### 2.2 Бизнес-логика сервисов
```python
# services/matching_service.py
class MatchingService:
    async def find_candidates(self, user_id: int, week_id: int) -> List[User]:
        # Алгоритм подбора с учетом времени и тем
        
# services/week_service.py  
class WeekService:
    async def register_user(self, user_id: int, week_type: str) -> WeekRegistration:
        # Проверка возможности регистрации
        
# services/feedback_service.py
class FeedbackService:
    async def can_register_again(self, user_id: int) -> bool:
        # Проверка обратной связи
```

## 📋 Этап 3: Telegram Bot разработка

### 3.1 Новые команды бота
```python
# Основные команды
/start              # Приветственное сообщение
/register           # Регистрация на неделю
/cancel             # Отмена регистрации
/match              # Подобрать пары
/pairs              # Мои пары
/feedback           # Оставить обратную связь
/profile            # Мой профиль
/help               # Справка
```

### 3.2 Интерактивные кнопки
```python
# Клавиатуры
WEEK_SELECTION_KEYBOARD = [
    ["Текущая неделя", "Следующая неделя"],
    ["Отмена"]
]

TOPIC_SELECTION_KEYBOARD = [
    # Динамически генерируется из дерева тем
]

CANDIDATE_SELECTION_KEYBOARD = [
    # 3 кандидата + кнопка "Еще варианты"
]

PAIR_ACTIONS_KEYBOARD = [
    ["Подтвердить", "Отклонить"]
]

FEEDBACK_KEYBOARD = [
    ["Оставить обратную связь", "Отменить пару"]
]
```

### 3.3 Обработчики состояний
```python
# Состояния для FSM (Finite State Machine)
class RegistrationStates(Enum):
    SELECTING_WEEK = "selecting_week"
    ENTERING_TIME = "entering_time" 
    SELECTING_TOPICS = "selecting_topics"
    CONFIRMING_REGISTRATION = "confirming_registration"

class FeedbackStates(Enum):
    ENTERING_FEEDBACK = "entering_feedback"
    RATING_SESSION = "rating_session"
```

## 📋 Этап 4: Алгоритм подбора пар

### 4.1 Логика матчинга
```python
def calculate_match_score(user1: User, user2: User) -> float:
    score = 0.0
    
    # Временное совпадение (вес: 0.4)
    time_match = calculate_time_compatibility(user1.preferred_time, user2.preferred_time)
    score += time_match * 0.4
    
    # Совпадение тем (вес: 0.3)
    topic_match = calculate_topic_overlap(user1.topics, user2.topics)
    score += topic_match * 0.3
    
    # Опыт (вес: 0.2)
    experience_match = calculate_experience_compatibility(user1.total_sessions, user2.total_sessions)
    score += experience_match * 0.2
    
    # Случайность (вес: 0.1)
    random_factor = random.uniform(0, 1)
    score += random_factor * 0.1
    
    return score
```

## 📋 Этап 5: Система обратной связи

### 5.1 Проверка возможности регистрации
```python
async def check_registration_eligibility(user_id: int) -> bool:
    # Первая регистрация - всегда доступна
    if not has_previous_registrations(user_id):
        return True
    
    # Проверяем обратную связь по всем занятиям
    total_sessions = get_total_sessions(user_id)
    feedback_given = get_feedback_count(user_id)
    
    return feedback_given >= total_sessions
```

## 📋 Этап 6: Уведомления и коммуникация

### 6.1 Система уведомлений
```python
# Типы уведомлений
class NotificationType(Enum):
    PAIR_REQUEST = "pair_request"
    PAIR_CONFIRMED = "pair_confirmed"
    PAIR_CANCELLED = "pair_cancelled"
    FEEDBACK_REMINDER = "feedback_reminder"
    WEEK_START = "week_start"
    WEEK_END = "week_end"
```

## 📋 Этап 7: Администрирование

### 7.1 Управление контентом
```python
# API для админов
POST /api/admin/content/update    # Обновить тексты
GET  /api/admin/stats             # Статистика
POST /api/admin/notifications     # Массовые уведомления
```

## 📅 Порядок реализации

### Неделя 1: База данных и базовый API
1. Создать миграции БД
2. Реализовать модели данных
3. Базовые CRUD операции
4. Система аутентификации

### Неделя 2: Основной функционал
1. Регистрация на недели
2. Выбор тем
3. Базовый алгоритм подбора пар
4. Telegram команды

### Неделя 3: Интерактивность
1. Интерактивные кнопки
2. FSM для сложных диалогов
3. Система уведомлений
4. Обратная связь

### Неделя 4: Полировка и тестирование
1. Улучшение алгоритма подбора
2. Тестирование всех сценариев
3. Обработка ошибок
4. Документация

## 🎯 Ключевые особенности

### Безопасность
- Первая регистрация - свободная
- Последующие требуют обратную связь
- JWT аутентификация
- Валидация всех входных данных

### Пользовательский опыт
- Интуитивные команды
- Интерактивные кнопки
- Мгновенные уведомления
- Простая навигация

### Масштабируемость
- Модульная архитектура
- Готовность к горизонтальному масштабированию
- Контейнеризация с Docker
- Структурированное логирование

## 📝 Статус реализации
- [x] Этап 1: База данных (модели и сервисы созданы)
- [x] Этап 2: Backend API (создан полный REST API, рефакторинг в модульную структуру)
- [x] Этап 3: Telegram Bot (создан полный интерфейс бота)
- [x] Этап 4: Алгоритм подбора (сервис создан)
- [ ] Этап 5: Обратная связь
- [ ] Этап 6: Уведомления
- [ ] Этап 7: Администрирование

### 🎯 Созданные API эндпоинты (модульная структура):

#### 👤 `profiles.py` - Профили пользователей
- `GET /orator/profile` - получить профиль
- `PUT /orator/profile` - обновить профиль
- `GET /orator/stats` - получить статистику

#### 📅 `weeks.py` - Регистрации на недели
- `POST /orator/weeks/register` - зарегистрироваться на неделю
- `GET /orator/weeks/current` - получить текущую регистрацию
- `DELETE /orator/weeks/cancel` - отменить регистрацию
- `GET /orator/weeks/info` - информация о неделе

#### 🎯 `topics.py` - Темы для тренировки
- `GET /orator/topics/tree` - получить дерево тем
- `GET /orator/topics/user` - темы пользователя

#### 🔍 `matching.py` - Подбор пар
- `POST /orator/matching/find` - найти кандидатов

#### 👥 `pairs.py` - Управление парами
- `POST /orator/pairs/create` - создать пару
- `POST /orator/pairs/{id}/confirm` - подтвердить пару
- `GET /orator/pairs/` - получить пары пользователя

#### 💬 `feedback.py` - Обратная связь
- `POST /orator/feedback/` - создать обратную связь
- `GET /orator/feedback/received` - полученная обратная связь
- `GET /orator/feedback/given` - данная обратная связь

#### 📝 `content.py` - Контент бота
- `GET /orator/content/{key}` - получить контент

#### ⚙️ `settings.py` - Настройки (админ)
- `GET /orator/settings/` - все настройки
- `PUT /orator/settings/{key}` - обновить настройку

### 🏗️ Архитектура API:
```
backend/api/orator/
├── __init__.py          # Главный роутер
├── profiles.py          # Профили пользователей
├── weeks.py            # Регистрации на недели
├── topics.py           # Темы для тренировки
├── matching.py         # Подбор пар
├── pairs.py            # Управление парами
├── feedback.py         # Обратная связь
├── content.py          # Контент бота
├── settings.py         # Настройки (админ)
└── README.md           # Документация
```

### 🤖 Архитектура Telegram Bot:
```
telegram-bot/
├── orator_bot.py              # Основной файл бота
├── orator_api_client.py       # API клиент для backend
├── orator_handlers.py         # Обработчики команд
├── orator_callback_handler.py # Обработчики callback
├── orator_translations.py     # Переводы (RU/EN)
├── config.py                  # Конфигурация
├── error_handler.py           # Обработка ошибок
├── exceptions.py              # Исключения
└── ORATOR_README.md           # Документация
```

### 📱 Команды Telegram Bot:
- `/start` - Запуск бота с главным меню
- `/help` - Справка по командам
- `/register` - Регистрация на неделю
- `/topics` - Выбор тем для тренировки
- `/find` - Поиск кандидатов для пары
- `/pairs` - Просмотр моих пар
- `/feedback` - Обратная связь
- `/profile` - Мой профиль
- `/stats` - Статистика тренировок
- `/cancel` - Отменить регистрацию
- `/en` - Переключить на английский
- `/ru` - Переключить на русский 