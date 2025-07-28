# Отчет об улучшении интерфейса "Мои пары"

## 🎯 Цель

Улучшить юзабельность интерфейса "Мои пары":
- Каждая пара - это кнопка
- При нажатии показываются действия для конкретной пары
- Логика подтверждения: только не-инициатор может подтвердить пару
- Добавить отдельный эндпоинт для отмены пары

## 🔧 Реализованная функциональность

### 📋 Новый интерфейс "Мои пары"

#### Список пар как кнопки:
```
Мои пары:

Выберите пару:

1. ✅ Анна Иванова (confirmed)
2. ⏳ Михаил Петров (pending)
3. ❌ Елена Сидорова (cancelled)

Назад
```

#### Детали пары с действиями:
```
👥 Пара с Михаил Петров
📊 Статус: ⏳ Ожидает подтверждения
🎯 Роль: Участник

✅ Подтвердить
❌ Отменить
💬 Обратная связь
⬅️ Назад к парам
```

### 🎮 Логика действий

1. **Подтверждение пары**: Доступно только если пользователь НЕ является инициатором пары
2. **Отмена пары**: Доступно для всех пользователей в паре
3. **Обратная связь**: Доступна для всех статусов пар

## 📝 Внесенные изменения

### 1. Новый API эндпоинт для отмены пары

#### Файл: `backend/api/orator/pairs.py`

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

### 2. Новый метод в базе данных

#### Файл: `backend/services/orator_database.py`

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

### 3. Обновлен метод получения пар

#### Файл: `backend/services/orator_database.py`

```python
async def get_user_pairs(self, user_id: UUID, week_start: date) -> List[Dict[str, Any]]:
    """Получить пары пользователя на неделю"""
    async with self.pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT 
                up.id, up.status, up.created_at, up.confirmed_at, up.cancelled_at,
                CASE 
                    WHEN up.user1_id = $1 THEN up.user2_id
                    ELSE up.user1_id
                END as partner_id,
                CASE 
                    WHEN up.user1_id = $1 THEN u2.first_name || ' ' || COALESCE(u2.last_name, '')
                    ELSE u1.first_name || ' ' || COALESCE(u1.last_name, '')
                END as partner_name,
                wr.week_start_date, wr.week_end_date,
                CASE 
                    WHEN up.user1_id = $1 THEN TRUE
                    ELSE FALSE
                END as is_initiator
            FROM user_pairs up
            JOIN week_registrations wr ON up.week_registration_id = wr.id
            JOIN users u1 ON up.user1_id = u1.id
            JOIN users u2 ON up.user2_id = u2.id
            WHERE (up.user1_id = $1 OR up.user2_id = $1) 
            AND wr.week_start_date = $2
            ORDER BY up.created_at DESC
            """,
            user_id,
            week_start,
        )
        return [dict(row) for row in rows]
```

### 4. Обновлена модель ответа

#### Файл: `backend/models/orator/pairs.py`

```python
class UserPairResponse(BaseModel):
    """Ответ с информацией о паре"""

    id: str
    partner_id: str
    partner_name: str
    week_start_date: date
    week_end_date: date
    status: PairStatus
    created_at: datetime
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    has_feedback: bool = False
    is_initiator: bool = False  # Новое поле

    @classmethod
    def from_user_pair(cls, user_pair: dict) -> "UserPairResponse":
        """Создать ответ из данных пары пользователей"""
        return cls(
            id=str(user_pair["id"]),
            partner_id=str(user_pair["partner_id"]),
            partner_name=user_pair["partner_name"],
            week_start_date=user_pair["week_start_date"],
            week_end_date=user_pair["week_end_date"],
            status=user_pair["status"],
            created_at=user_pair["created_at"],
            confirmed_at=user_pair.get("confirmed_at"),
            cancelled_at=user_pair.get("cancelled_at"),
            has_feedback=user_pair.get("has_feedback", False),
            is_initiator=user_pair.get("is_initiator", False)  # Новое поле
        )
```

### 5. Добавлен метод в API клиент

#### Файл: `telegram-bot/orator_api_client.py`

```python
async def cancel_pair(self, pair_id: str) -> Dict[str, Any]:
    """Отменить пару"""
    return await self._make_request("POST", f"/api/v1/orator/pairs/{pair_id}/cancel")
```

### 6. Обновлен интерфейс Telegram бота

#### Файл: `telegram-bot/orator_callback_handler.py`

##### Новый метод `_handle_pairs_callback`:
```python
async def _handle_pairs_callback(self, query, language: str):
    """Обработка просмотра пар"""
    pairs = await self.api_client.get_user_pairs()

    if not pairs:
        await query.edit_message_text(get_text("pairs_empty", language))
        return

    # Формируем список пар как кнопки
    pairs_text = get_text("pairs_welcome", language) + "\n\nВыберите пару:"
    keyboard = []
    
    for i, pair in enumerate(pairs[:5], 1):
        partner_name = pair.get("partner_name", "Пользователь")
        status = pair.get("status", "unknown")
        pair_id = pair.get("id")

        status_emoji = "✅" if status == "confirmed" else "⏳" if status == "pending" else "❌"
        button_text = f"{i}. {status_emoji} {partner_name} ({status})"
        
        # Каждая пара - это кнопка
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"pair_details_{pair_id}")])

    keyboard.append([InlineKeyboardButton(get_button_text("back", language), callback_data="start")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(pairs_text, reply_markup=reply_markup, parse_mode="HTML")
```

##### Новый метод `_handle_pair_details`:
```python
async def _handle_pair_details(self, query, callback_data: str, language: str):
    """Обработка деталей пары"""
    pair_id = callback_data.replace("pair_details_", "")
    
    # Получаем информацию о паре
    pairs = await self.api_client.get_user_pairs()
    target_pair = None
    for pair in pairs:
        if pair.get("id") == pair_id:
            target_pair = pair
            break
    
    if not target_pair:
        await query.edit_message_text("❌ Пара не найдена", parse_mode="HTML")
        return

    partner_name = target_pair.get("partner_name", "Пользователь")
    status = target_pair.get("status", "unknown")
    is_initiator = target_pair.get("is_initiator", False)
    
    # Формируем текст с информацией о паре
    status_emoji = "✅" if status == "confirmed" else "⏳" if status == "pending" else "❌"
    status_text = "Подтверждена" if status == "confirmed" else "Ожидает подтверждения" if status == "pending" else "Отменена"
    
    pair_info = f"👥 Пара с {partner_name}\n"
    pair_info += f"📊 Статус: {status_emoji} {status_text}\n"
    pair_info += f"🎯 Роль: {'Инициатор' if is_initiator else 'Участник'}\n"
    
    # Создаем кнопки действий
    keyboard = []
    
    if status == "pending":
        if not is_initiator:
            # Если пользователь не инициатор - может подтвердить
            keyboard.append([InlineKeyboardButton("✅ Подтвердить", callback_data=f"pair_confirm_{pair_id}")])
        # Любой может отменить
        keyboard.append([InlineKeyboardButton("❌ Отменить", callback_data=f"pair_cancel_{pair_id}")])
    
    # Обратная связь доступна для всех статусов
    keyboard.append([InlineKeyboardButton("💬 Обратная связь", callback_data=f"pair_feedback_{pair_id}")])
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton("⬅️ Назад к парам", callback_data="pairs")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(pair_info, reply_markup=reply_markup, parse_mode="HTML")
```

##### Обновленный метод `_handle_pair_cancel`:
```python
async def _handle_pair_cancel(self, query, callback_data: str, language: str):
    """Обработка отмены пары"""
    pair_id = callback_data.replace("pair_cancel_", "")

    try:
        # Отменяем пару через новый API
        await self.api_client.cancel_pair(pair_id)
        await query.edit_message_text("❌ Пара отменена", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Cancel pair error: {e}")
        await query.edit_message_text("❌ Ошибка при отмене пары", parse_mode="HTML")
```

### 7. Добавлены новые callback'ы

```python
elif callback_data.startswith("pair_details_"):
    await self._handle_pair_details(query, callback_data, language)
```

## 🎨 Пользовательский интерфейс

### Пример навигации:

1. **Пользователь выбирает "Мои пары"**
   ```
   Мои пары:
   
   Выберите пару:
   
   1. ✅ Анна Иванова (confirmed)
   2. ⏳ Михаил Петров (pending)
   3. ❌ Елена Сидорова (cancelled)
   
   Назад
   ```

2. **Пользователь нажимает на пару "Михаил Петров"**
   ```
   👥 Пара с Михаил Петров
   📊 Статус: ⏳ Ожидает подтверждения
   🎯 Роль: Участник
   
   ✅ Подтвердить
   ❌ Отменить
   💬 Обратная связь
   ⬅️ Назад к парам
   ```

3. **Если пользователь инициатор пары**
   ```
   👥 Пара с Анна Иванова
   📊 Статус: ⏳ Ожидает подтверждения
   🎯 Роль: Инициатор
   
   ❌ Отменить
   💬 Обратная связь
   ⬅️ Назад к парам
   ```

## 🔄 Логика работы

1. **Пользователь выбирает "Мои пары"** → Показывается список пар как кнопки
2. **Пользователь нажимает на пару** → Показываются детали пары с доступными действиями
3. **Логика подтверждения**:
   - Если пользователь НЕ инициатор → Кнопка "Подтвердить" доступна
   - Если пользователь инициатор → Кнопка "Подтвердить" скрыта
4. **Логика отмены**: Кнопка "Отменить" доступна всем участникам пары
5. **Обратная связь**: Доступна для всех статусов пар

## ✅ Результат

**ИНТЕРФЕЙС "МОИ ПАРЫ" УЛУЧШЕН!**

- ✅ Каждая пара - это кнопка для лучшей навигации
- ✅ Детальный просмотр пары с информацией о статусе и роли
- ✅ Логика подтверждения: только не-инициатор может подтвердить
- ✅ Отдельный API эндпоинт для отмены пары
- ✅ Новое поле `is_initiator` в модели ответа
- ✅ Улучшенная обработка ошибок
- ✅ Backend и бот перезапущены с новыми изменениями

## 🧪 Тестирование

Новая функциональность готова к тестированию:
1. Выберите "Мои пары" в боте
2. Увидите список пар как кнопки
3. Нажмите на любую пару
4. Увидите детали пары с доступными действиями
5. Попробуйте подтвердить/отменить пару в зависимости от вашей роли

## 📝 Следующие шаги

1. Протестировать новый интерфейс в Telegram боте
2. Добавить уведомления партнеру о подтверждении/отмене пары
3. Добавить текстовую обратную связь (не только рейтинг)
4. Реализовать просмотр истории пар 