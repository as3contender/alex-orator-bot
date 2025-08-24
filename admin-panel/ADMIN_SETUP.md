# Настройка системы аутентификации администраторов

## Обзор изменений

Система аутентификации администраторов была переработана для хранения данных в базе данных вместо хардкода в коде.

## Что изменилось

1. **Создана таблица `admin_users`** в базе данных `app_db`
2. **Обновлен класс `AdminAuth`** для работы с базой данных
3. **Добавлены методы** в `AdminDatabase` для управления администраторами
4. **Убрана зависимость** от хардкоденных учетных данных

## Структура таблицы admin_users

```sql
CREATE TABLE admin_users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin' CHECK (role IN ('admin', 'super_admin', 'moderator')),
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Учетные данные по умолчанию

- **Логин:** `admin`
- **Пароль:** `admin123`
- **Роль:** `super_admin`

## Установка и настройка

### 1. Создание таблицы в базе данных

Запустите скрипт инициализации:

```bash
cd admin_panel
python init_admin_db.py
```

### 2. Проверка подключения

Убедитесь, что Docker контейнеры запущены и база данных доступна:

```bash
docker ps
```

### 3. Запуск административной панели

```bash
cd admin_panel
streamlit run admin_app.py
```

## Роли администраторов

- **`admin`** - Обычный администратор
- **`super_admin`** - Супер-администратор (полные права)
- **`moderator`** - Модератор (ограниченные права)

## Безопасность

- Пароли хешируются с использованием SHA-256
- JWT токены с ограниченным временем жизни (30 минут)
- Автоматическое обновление времени последнего входа
- Мягкое удаление (деактивация) вместо физического удаления

## Добавление новых администраторов

### Через код:

```python
from auth import hash_password
from database import get_db

db = get_db()
hashed_password = hash_password("new_password")
db.create_admin_user(
    username="new_admin",
    hashed_password=hashed_password,
    full_name="Новый администратор",
    role="admin"
)
```

### Через SQL:

```sql
INSERT INTO admin_users (username, hashed_password, full_name, role)
VALUES (
    'new_admin',
    'хеш_пароля',
    'Новый администратор',
    'admin'
);
```

## Устранение неполадок

### Ошибка подключения к базе данных

1. Проверьте, что Docker контейнеры запущены
2. Убедитесь, что база данных доступна на порту 5434
3. Проверьте правильность пароля в `database.py`

### Ошибка аутентификации

1. Проверьте, что таблица `admin_users` создана
2. Убедитесь, что администратор по умолчанию добавлен
3. Проверьте логи на наличие ошибок

### Ошибка создания таблицы

1. Убедитесь, что у пользователя `alex_orator` есть права на создание таблиц
2. Проверьте, что расширение `uuid-ossp` доступно
3. Проверьте логи PostgreSQL

## Логирование

Все операции с администраторами логируются в консоль с эмодзи для удобства:

- ✅ Успешные операции
- ❌ Ошибки
- 🔗 Подключения к базе данных
- 📊 Статистика
- 🔐 Операции аутентификации
