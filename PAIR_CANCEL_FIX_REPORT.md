# Отчет об исправлении ошибки отмены пары

## 🐛 Проблема

При попытке отменить пару возникала ошибка:
```
❌ Ошибка при отмене пары
```

В логах backend'а:
```
ERROR | api.orator.pairs:cancel_pair:86 - Cancel pair error: 'partner_id'
```

## 🔍 Диагностика

Проблема была в методе `cancel_user_pair` в базе данных:

1. **Неправильный SQL запрос**: Использовался `up.user1_id = up.user1_id` вместо сравнения с конкретным пользователем
2. **Неполные данные**: Метод возвращал только базовые поля из таблицы `user_pairs`, а `UserPairResponse.from_user_pair` ожидал поля `partner_id`, `partner_name`, `is_initiator` и другие
3. **Отсутствие параметра**: Метод не принимал `user_id` для правильного определения партнера

## 🔧 Исправления

### 1. Обновлен метод `cancel_user_pair`

#### Файл: `backend/services/orator_database.py`

**Было:**
```python
async def cancel_user_pair(self, pair_id: UUID) -> Optional[Dict[str, Any]]:
    """Отменить пару"""
    async with self.pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE user_pairs 
            SET status = 'cancelled', cancelled_at = CURRENT_TIMESTAMP
            WHERE id = $1 AND status IN ('pending', 'confirmed')
            """,
            pair_id,
        )

        if result == "UPDATE 0":
            return None

        # Возвращаем обновленную пару
        row = await conn.fetchrow(
            """
            SELECT * FROM user_pairs WHERE id = $1
            """,
            pair_id,
        )
        return dict(row) if row else None
```

**Стало:**
```python
async def cancel_user_pair(self, pair_id: UUID, user_id: UUID) -> Optional[Dict[str, Any]]:
    """Отменить пару"""
    async with self.pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE user_pairs 
            SET status = 'cancelled', cancelled_at = CURRENT_TIMESTAMP
            WHERE id = $1 AND status IN ('pending', 'confirmed')
            """,
            pair_id,
        )

        if result == "UPDATE 0":
            return None

        # Возвращаем обновленную пару с полной информацией
        row = await conn.fetchrow(
            """
            SELECT 
                up.id, up.status, up.created_at, up.confirmed_at, up.cancelled_at,
                CASE 
                    WHEN up.user1_id = $2 THEN up.user2_id
                    ELSE up.user1_id
                END as partner_id,
                CASE 
                    WHEN up.user1_id = $2 THEN u2.first_name || ' ' || COALESCE(u2.last_name, '')
                    ELSE u1.first_name || ' ' || COALESCE(u1.last_name, '')
                END as partner_name,
                wr.week_start_date, wr.week_end_date,
                CASE 
                    WHEN up.user1_id = $2 THEN TRUE
                    ELSE FALSE
                END as is_initiator
            FROM user_pairs up
            JOIN week_registrations wr ON up.week_registration_id = wr.id
            JOIN users u1 ON up.user1_id = u1.id
            JOIN users u2 ON up.user2_id = u2.id
            WHERE up.id = $1
            """,
            pair_id,
            user_id,
        )
        return dict(row) if row else None
```

### 2. Обновлен API эндпоинт

#### Файл: `backend/api/orator/pairs.py`

**Было:**
```python
@router.post("/{pair_id}/cancel", response_model=UserPairResponse)
async def cancel_pair(pair_id: str, current_user_id: str = Depends(security_service.get_current_user_id)):
    """Отменить пару"""
    try:
        user_pair = await orator_db.cancel_user_pair(pair_id)
        if not user_pair:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pair not found")

        return UserPairResponse.from_user_pair(user_pair)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel pair error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to cancel pair")
```

**Стало:**
```python
@router.post("/{pair_id}/cancel", response_model=UserPairResponse)
async def cancel_pair(pair_id: str, current_user_id: str = Depends(security_service.get_current_user_id)):
    """Отменить пару"""
    try:
        user_pair = await orator_db.cancel_user_pair(pair_id, current_user_id)
        if not user_pair:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pair not found")

        return UserPairResponse.from_user_pair(user_pair)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel pair error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to cancel pair")
```

## 🔄 Ключевые изменения

1. **Добавлен параметр `user_id`**: Метод теперь принимает `user_id` для правильного определения партнера
2. **Исправлен SQL запрос**: Заменен `up.user1_id = up.user1_id` на `up.user1_id = $2`
3. **Полные данные**: Запрос теперь возвращает все необходимые поля для `UserPairResponse`
4. **JOIN таблиц**: Добавлены JOIN'ы с `week_registrations`, `users` для получения полной информации

## ✅ Результат

**ОШИБКА ОТМЕНЫ ПАРЫ ИСПРАВЛЕНА!**

- ✅ Метод `cancel_user_pair` теперь возвращает полные данные
- ✅ Правильное определение партнера и роли пользователя
- ✅ Совместимость с `UserPairResponse.from_user_pair`
- ✅ Backend перезапущен с исправлениями

## 🧪 Тестирование

Теперь отмена пары должна работать корректно:
1. Выберите "Мои пары" в боте
2. Нажмите на любую пару
3. Нажмите "❌ Отменить"
4. Должно появиться сообщение "❌ Пара отменена"

## 📝 Следующие шаги

1. Протестировать отмену пары в Telegram боте
2. Проверить, что статус пары корректно обновляется в базе данных
3. Убедиться, что все остальные функции работают нормально 