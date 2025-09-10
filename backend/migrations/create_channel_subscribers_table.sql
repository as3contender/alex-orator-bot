-- Создание таблицы для отслеживания подписчиков каналов
CREATE TABLE IF NOT EXISTS channel_subscribers (
    id SERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('member', 'left', 'kicked', 'administrator', 'creator')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Уникальный индекс для предотвращения дублирования записей
    UNIQUE(chat_id, user_id)
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_channel_subscribers_chat_id ON channel_subscribers(chat_id);
CREATE INDEX IF NOT EXISTS idx_channel_subscribers_user_id ON channel_subscribers(user_id);
CREATE INDEX IF NOT EXISTS idx_channel_subscribers_status ON channel_subscribers(status);
CREATE INDEX IF NOT EXISTS idx_channel_subscribers_updated_at ON channel_subscribers(updated_at);

-- Комментарии к таблице
COMMENT ON TABLE channel_subscribers IS 'Таблица для отслеживания подписчиков каналов';
COMMENT ON COLUMN channel_subscribers.chat_id IS 'ID чата/канала';
COMMENT ON COLUMN channel_subscribers.user_id IS 'ID пользователя';
COMMENT ON COLUMN channel_subscribers.status IS 'Статус пользователя в канале';
COMMENT ON COLUMN channel_subscribers.created_at IS 'Дата создания записи';
COMMENT ON COLUMN channel_subscribers.updated_at IS 'Дата последнего обновления записи';
