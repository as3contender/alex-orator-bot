# Отчет об изменении логики обратной связи

## 🎯 Цель

Изменить логику обратной связи: обратная связь должна оставляться на пару, а не на конкретного пользователя.

## 🔄 Изменения в логике

### Было:
- Обратная связь привязана к конкретному пользователю (`to_user_id`)
- Пользователь оставляет обратную связь другому пользователю

### Стало:
- Обратная связь привязана к паре (`pair_id`)
- Пользователь оставляет обратную связь на пару/занятие

## 📝 Внесенные изменения

### 1. Обновлена схема базы данных

#### Файл: `backend/services/orator_database.py`

**Было:**
```sql
CREATE TABLE IF NOT EXISTS session_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pair_id UUID REFERENCES user_pairs(id) ON DELETE CASCADE,
    from_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    to_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    feedback_text TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Стало:**
```sql
CREATE TABLE IF NOT EXISTS session_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pair_id UUID REFERENCES user_pairs(id) ON DELETE CASCADE,
    from_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    feedback_text TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### 2. Обновлена модель данных

#### Файл: `backend/models/orator/feedback.py`

**Было:**
```python
class SessionFeedbackCreate(BaseModel):
    """Создание обратной связи"""
    pair_id: str
    to_user_id: str  # Убрано
    feedback_text: str = Field(..., min_length=3, max_length=1000)
    rating: FeedbackRating

class SessionFeedback(BaseEntity):
    """Обратная связь по занятию"""
    pair_id: str
    from_user_id: str
    to_user_id: str  # Убрано
    feedback_text: str = Field(..., min_length=3, max_length=1000)
    rating: FeedbackRating
```

**Стало:**
```python
class SessionFeedbackCreate(BaseModel):
    """Создание обратной связи"""
    pair_id: str
    feedback_text: str = Field(..., min_length=3, max_length=1000)
    rating: FeedbackRating

class SessionFeedback(BaseEntity):
    """Обратная связь по занятию"""
    pair_id: str
    from_user_id: str
    feedback_text: str = Field(..., min_length=3, max_length=1000)
    rating: FeedbackRating
```

### 3. Обновлен метод создания обратной связи

#### Файл: `backend/services/orator_database.py`

**Было:**
```python
async def create_session_feedback(
    self, pair_id: UUID, from_user_id: UUID, to_user_id: UUID, feedback_text: str, rating: int
) -> Optional[Dict[str, Any]]:
    """Создать обратную связь по занятию"""
    async with self.pool.acquire() as conn:
        feedback_id = await conn.fetchval(
            """
            INSERT INTO session_feedback 
            (pair_id, from_user_id, to_user_id, feedback_text, rating)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            pair_id,
            from_user_id,
            to_user_id,
            feedback_text,
            rating,
        )
```

**Стало:**
```python
async def create_session_feedback(
    self, pair_id: UUID, from_user_id: UUID, feedback_text: str, rating: int
) -> Optional[Dict[str, Any]]:
    """Создать обратную связь по занятию"""
    async with self.pool.acquire() as conn:
        feedback_id = await conn.fetchval(
            """
            INSERT INTO session_feedback 
            (pair_id, from_user_id, feedback_text, rating)
            VALUES ($1, $2, $3, $4)
            RETURNING id
            """,
            pair_id,
            from_user_id,
            feedback_text,
            rating,
        )
```

### 4. Обновлен API эндпоинт

#### Файл: `backend/api/orator/feedback.py`

**Было:**
```python
feedback = await orator_db.create_session_feedback(
    pair_id=feedback_data.pair_id,
    from_user_id=current_user_id,
    to_user_id=feedback_data.to_user_id,  # Убрано
    feedback_text=feedback_data.feedback_text,
    rating=feedback_data.rating,
)
```

**Стало:**
```python
feedback = await orator_db.create_session_feedback(
    pair_id=feedback_data.pair_id,
    from_user_id=current_user_id,
    feedback_text=feedback_data.feedback_text,
    rating=feedback_data.rating,
)
```

### 5. Обновлен Telegram бот

#### Файл: `telegram-bot/orator_callback_handler.py`

**Было:**
```python
feedback_data = {
    "pair_id": pair_id,
    "to_user_id": target_pair.get("partner_id"),  # Убрано
    "rating": rating,
    "feedback_text": f"Оценка: {rating} звезд",
}
```

**Стало:**
```python
feedback_data = {
    "pair_id": pair_id,
    "rating": rating,
    "feedback_text": f"Оценка: {rating} звезд",
}
```

### 6. Обновлена логика получения обратной связи

#### Файл: `backend/services/orator_database.py`

**Новая логика для полученной обратной связи:**
```python
# Получить полученную обратную связь (оставленную другими пользователями для пар, где участвует данный пользователь)
rows = await conn.fetch(
    """
    SELECT 
        sf.id, sf.pair_id, sf.feedback_text, sf.rating, sf.created_at,
        u.first_name || ' ' || COALESCE(u.last_name, '') as from_user_name
    FROM session_feedback sf
    JOIN user_pairs up ON sf.pair_id = up.id
    JOIN users u ON sf.from_user_id = u.id
    WHERE (up.user1_id = $1 OR up.user2_id = $1) AND sf.from_user_id != $1
    ORDER BY sf.created_at DESC
    """,
    to_user_id,
)
```

### 7. Добавлен метод для модели ответа

#### Файл: `backend/models/orator/feedback.py`

```python
@classmethod
def from_session_feedback(cls, feedback: dict) -> "SessionFeedbackResponse":
    """Создать ответ из данных обратной связи"""
    return cls(
        id=str(feedback["id"]),
        from_user_name=feedback.get("from_user_name", "Пользователь"),
        feedback_text=feedback["feedback_text"],
        rating=feedback["rating"],
        created_at=feedback["created_at"]
    )
```

## 🔄 Новая логика работы

### Создание обратной связи:
1. Пользователь выбирает пару
2. Нажимает "💬 Обратная связь"
3. Выбирает рейтинг (1-5 звезд)
4. Обратная связь сохраняется для пары

### Получение обратной связи:
- **Данная обратная связь**: Показывает обратную связь, которую пользователь оставил для своих пар
- **Полученная обратная связь**: Показывает обратную связь, которую другие пользователи оставили для пар, где участвует данный пользователь

## ✅ Результат

**ЛОГИКА ОБРАТНОЙ СВЯЗИ ИЗМЕНЕНА НА ПАРЫ!**

- ✅ Убрано поле `to_user_id` из схемы базы данных
- ✅ Обратная связь теперь привязана к парам, а не к пользователям
- ✅ Обновлены все модели и API эндпоинты
- ✅ Обновлена логика получения обратной связи
- ✅ Backend перезапущен с изменениями

## 🧪 Тестирование

Теперь обратная связь должна работать с новой логикой:
1. Выберите "Мои пары"
2. Нажмите на пару
3. Нажмите "💬 Обратная связь"
4. Выберите рейтинг (1-5 звезд)
5. Обратная связь сохранится для пары

## 📝 Следующие шаги

1. Протестировать создание обратной связи для пар
2. Протестировать просмотр полученной и данной обратной связи
3. Убедиться, что логика работает корректно для всех пользователей в паре 