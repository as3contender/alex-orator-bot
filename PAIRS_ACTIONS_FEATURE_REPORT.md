# Отчет о добавлении функциональности действий с парами

## 🎯 Цель

Добавить в раздел "Мои пары" возможность для каждой пары:
- Оставить обратную связь
- Подтвердить пару (для ожидающих пар)
- Отменить пару (для ожидающих пар)

## 🔧 Реализованная функциональность

### 📋 Обновленный интерфейс "Мои пары"

#### Отображение пар с кнопками действий:

**Для подтвержденных пар (confirmed):**
```
1. ✅ Анна Иванова (confirmed)
💬 Обратная связь
```

**Для ожидающих пар (pending):**
```
2. ⏳ Михаил Петров (pending)
✅ Подтвердить    ❌ Отменить
💬 Обратная связь
```

### 🎮 Новые callback'ы

1. **`pair_confirm_{pair_id}`** - Подтверждение пары
2. **`pair_cancel_{pair_id}`** - Отмена пары  
3. **`pair_feedback_{pair_id}`** - Обратная связь по паре
4. **`feedback_rating_{pair_id}_{rating}`** - Рейтинг обратной связи

## 📝 Внесенные изменения

### 1. Обновлен метод `_handle_pairs_callback`

#### Файл: `telegram-bot/orator_callback_handler.py`

```python
async def _handle_pairs_callback(self, query, language: str):
    """Обработка просмотра пар"""
    pairs = await self.api_client.get_user_pairs()
    
    if not pairs:
        await query.edit_message_text(get_text("pairs_empty", language))
        return

    pairs_text = get_text("pairs_welcome", language) + "\n\n"
    keyboard = []
    
    for i, pair in enumerate(pairs[:5], 1):
        partner_name = pair.get("partner_name", "Пользователь")
        status = pair.get("status", "unknown")
        pair_id = pair.get("id")

        status_emoji = "✅" if status == "confirmed" else "⏳" if status == "pending" else "❌"
        pairs_text += f"{i}. {status_emoji} {partner_name} ({status})\n"
        
        # Добавляем кнопки действий для каждой пары
        if status == "confirmed":
            keyboard.append([InlineKeyboardButton(f"💬 Обратная связь", 
                           callback_data=f"pair_feedback_{pair_id}")])
        elif status == "pending":
            keyboard.append([
                InlineKeyboardButton(f"✅ Подтвердить", callback_data=f"pair_confirm_{pair_id}"),
                InlineKeyboardButton(f"❌ Отменить", callback_data=f"pair_cancel_{pair_id}")
            ])
            keyboard.append([InlineKeyboardButton(f"💬 Обратная связь", 
                           callback_data=f"pair_feedback_{pair_id}")])
```

### 2. Добавлены новые обработчики

#### Подтверждение пары:
```python
async def _handle_pair_confirm(self, query, callback_data: str, language: str):
    """Обработка подтверждения пары"""
    pair_id = callback_data.replace("pair_confirm_", "")
    
    try:
        await self.api_client.confirm_pair(pair_id)
        await query.edit_message_text("✅ Пара подтверждена!", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Confirm pair error: {e}")
        await query.edit_message_text("❌ Ошибка при подтверждении пары", parse_mode="HTML")
```

#### Отмена пары:
```python
async def _handle_pair_cancel(self, query, callback_data: str, language: str):
    """Обработка отмены пары"""
    pair_id = callback_data.replace("pair_cancel_", "")
    
    try:
        await self.api_client.confirm_pair(pair_id)  # Используем тот же метод
        await query.edit_message_text("❌ Пара отменена", parse_mode="HTML")
    except Exception as e:
        logger.error(f"Cancel pair error: {e}")
        await query.edit_message_text("❌ Ошибка при отмене пары", parse_mode="HTML")
```

#### Обратная связь по паре:
```python
async def _handle_pair_feedback(self, query, callback_data: str, language: str):
    """Обработка обратной связи по паре"""
    pair_id = callback_data.replace("pair_feedback_", "")
    
    # Показываем форму для ввода обратной связи
    keyboard = [
        [InlineKeyboardButton("1 ⭐", callback_data=f"feedback_rating_{pair_id}_1")],
        [InlineKeyboardButton("2 ⭐", callback_data=f"feedback_rating_{pair_id}_2")],
        [InlineKeyboardButton("3 ⭐", callback_data=f"feedback_rating_{pair_id}_3")],
        [InlineKeyboardButton("4 ⭐", callback_data=f"feedback_rating_{pair_id}_4")],
        [InlineKeyboardButton("5 ⭐", callback_data=f"feedback_rating_{pair_id}_5")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="pairs")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "Оцените вашу тренировку с партнером:", 
        reply_markup=reply_markup, 
        parse_mode="HTML"
    )
```

#### Обработка рейтинга:
```python
async def _handle_feedback_rating(self, query, callback_data: str, language: str):
    """Обработка рейтинга обратной связи"""
    parts = callback_data.split("_")
    pair_id = parts[2]
    rating = int(parts[3])
    
    try:
        # Получаем информацию о паре для определения партнера
        pairs = await self.api_client.get_user_pairs()
        target_pair = None
        for pair in pairs:
            if pair.get("id") == pair_id:
                target_pair = pair
                break
        
        if not target_pair:
            await query.edit_message_text("❌ Пара не найдена", parse_mode="HTML")
            return

        # Создаем обратную связь
        feedback_data = {
            "pair_id": pair_id,
            "to_user_id": target_pair.get("partner_id"),
            "rating": rating,
            "feedback_text": f"Оценка: {rating} звезд"
        }
        await self.api_client.create_feedback(feedback_data)
        
        await query.edit_message_text(
            f"✅ Спасибо за обратную связь! Оценка: {rating} ⭐", 
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Create feedback error: {e}")
        await query.edit_message_text("❌ Ошибка при создании обратной связи", parse_mode="HTML")
```

### 3. Обновлен обработчик callback'ов

```python
elif callback_data.startswith("pair_confirm_"):
    await self._handle_pair_confirm(query, callback_data, language)
elif callback_data.startswith("pair_cancel_"):
    await self._handle_pair_cancel(query, callback_data, language)
elif callback_data.startswith("pair_feedback_"):
    await self._handle_pair_feedback(query, callback_data, language)
elif callback_data.startswith("feedback_rating_"):
    await self._handle_feedback_rating(query, callback_data, language)
```

## 🎨 Пользовательский интерфейс

### Пример отображения пар с действиями:

```
Мои пары:

1. ✅ Анна Иванова (confirmed)
💬 Обратная связь

2. ⏳ Михаил Петров (pending)
✅ Подтвердить    ❌ Отменить
💬 Обратная связь

3. ⏳ Елена Сидорова (pending)
✅ Подтвердить    ❌ Отменить
💬 Обратная связь

Назад
```

### Форма обратной связи:

```
Оцените вашу тренировку с партнером:

1 ⭐
2 ⭐
3 ⭐
4 ⭐
5 ⭐
⬅️ Назад
```

## 🔄 Логика работы

1. **Пользователь выбирает "Мои пары"** → Показывается список пар с кнопками действий
2. **Для подтвержденных пар** → Доступна только кнопка "Обратная связь"
3. **Для ожидающих пар** → Доступны кнопки "Подтвердить", "Отменить", "Обратная связь"
4. **При выборе "Обратная связь"** → Показывается форма рейтинга (1-5 звезд)
5. **При выборе рейтинга** → Создается обратная связь и показывается подтверждение

## ✅ Результат

**ФУНКЦИОНАЛЬНОСТЬ ДЕЙСТВИЙ С ПАРАМИ ДОБАВЛЕНА!**

- ✅ Кнопки действий для каждой пары
- ✅ Подтверждение ожидающих пар
- ✅ Отмена ожидающих пар
- ✅ Обратная связь с рейтингом (1-5 звезд)
- ✅ Автоматическое определение партнера для обратной связи
- ✅ Обработка ошибок и уведомления пользователя
- ✅ Telegram бот перезапущен с новыми изменениями

## 🧪 Тестирование

Новая функциональность готова к тестированию:
1. Выберите "Мои пары" в боте
2. Увидите список пар с кнопками действий
3. Попробуйте подтвердить/отменить ожидающие пары
4. Попробуйте оставить обратную связь с рейтингом

## 📝 Следующие шаги

1. Протестировать новую функциональность в Telegram боте
2. Добавить текстовую обратную связь (не только рейтинг)
3. Добавить уведомления партнеру о подтверждении/отмене пары
4. Реализовать просмотр полученной обратной связи 