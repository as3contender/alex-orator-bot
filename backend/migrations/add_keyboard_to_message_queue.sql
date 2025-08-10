-- Миграция: добавление поля keyboard в таблицу message_queue
-- Выполнить: psql -d your_database -f add_keyboard_to_message_queue.sql

-- Добавляем поле keyboard типа JSONB
ALTER TABLE message_queue ADD COLUMN IF NOT EXISTS keyboard JSONB DEFAULT '{}';

-- Комментарий к полю
COMMENT ON COLUMN message_queue.keyboard IS 'JSON-структура клавиатуры для Telegram сообщений';
