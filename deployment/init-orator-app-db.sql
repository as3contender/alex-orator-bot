-- Инициализация базы данных Alex Orator Bot
-- Этот скрипт создает все необходимые таблицы для работы бота

-- Включение расширения для UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- ОСНОВНЫЕ ТАБЛИЦЫ ПОЛЬЗОВАТЕЛЕЙ
-- ============================================================================

-- Таблица пользователей (расширенная для Telegram)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id VARCHAR(100) UNIQUE NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    gender VARCHAR(10) CHECK (gender IN ('male', 'female', 'other')),
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_sessions INTEGER DEFAULT 0,
    feedback_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- РЕГИСТРАЦИИ НА НЕДЕЛИ
-- ============================================================================

-- Таблица регистраций на недели
CREATE TABLE IF NOT EXISTS week_registrations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    week_start_date DATE NOT NULL,
    week_end_date DATE NOT NULL,
    preferred_time_msk VARCHAR(5) NOT NULL, -- формат HH:MM
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'cancelled')),
    cancelled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ТЕМЫ
-- ============================================================================

-- Таблица выбранных тем пользователей
CREATE TABLE IF NOT EXISTS user_topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    week_registration_id UUID REFERENCES week_registrations(id) ON DELETE CASCADE,
    topic_path VARCHAR(500) NOT NULL, -- путь к теме, например: 'Подача - Темы речи уровень 1'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ПАРЫ ПОЛЬЗОВАТЕЛЕЙ
-- ============================================================================

-- Таблица пар пользователей
CREATE TABLE IF NOT EXISTS user_pairs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user1_id UUID REFERENCES users(id) ON DELETE CASCADE,
    user2_id UUID REFERENCES users(id) ON DELETE CASCADE,
    week_registration_id UUID REFERENCES week_registrations(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'cancelled')),
    confirmed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ОБРАТНАЯ СВЯЗЬ
-- ============================================================================

-- Таблица обратной связи по занятиям
CREATE TABLE IF NOT EXISTS session_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pair_id UUID REFERENCES user_pairs(id) ON DELETE CASCADE,
    from_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    to_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    feedback_text TEXT NOT NULL CHECK (length(feedback_text) >= 3 AND length(feedback_text) <= 1000),
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- КОНТЕНТ БОТА
-- ============================================================================

-- Таблица контента бота (тексты, сообщения)
CREATE TABLE IF NOT EXISTS bot_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content_key VARCHAR(100) NOT NULL UNIQUE, -- ключ контента, например: 'welcome_message'
    content_text TEXT NOT NULL, -- текст с поддержкой markdown
    language VARCHAR(10) DEFAULT 'ru',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- НАСТРОЙКИ БОТА
-- ============================================================================

-- Таблица настроек ораторского бота
CREATE TABLE IF NOT EXISTS orator_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(100) NOT NULL UNIQUE,
    value TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ИНДЕКСЫ ДЛЯ ОПТИМИЗАЦИИ
-- ============================================================================

-- Индексы для таблицы пользователей
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_gender ON users(gender);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Индексы для таблицы регистраций
CREATE INDEX IF NOT EXISTS idx_week_registrations_user_id ON week_registrations(user_id);
CREATE INDEX IF NOT EXISTS idx_week_registrations_week_dates ON week_registrations(week_start_date, week_end_date);
CREATE INDEX IF NOT EXISTS idx_week_registrations_status ON week_registrations(status);

-- Индексы для таблицы тем
CREATE INDEX IF NOT EXISTS idx_user_topics_user_id ON user_topics(user_id);
CREATE INDEX IF NOT EXISTS idx_user_topics_week_registration_id ON user_topics(week_registration_id);

-- Индексы для таблицы пар
CREATE INDEX IF NOT EXISTS idx_user_pairs_user1_id ON user_pairs(user1_id);
CREATE INDEX IF NOT EXISTS idx_user_pairs_user2_id ON user_pairs(user2_id);
CREATE INDEX IF NOT EXISTS idx_user_pairs_week_registration_id ON user_pairs(week_registration_id);
CREATE INDEX IF NOT EXISTS idx_user_pairs_status ON user_pairs(status);

-- Индексы для таблицы обратной связи
CREATE INDEX IF NOT EXISTS idx_session_feedback_pair_id ON session_feedback(pair_id);
CREATE INDEX IF NOT EXISTS idx_session_feedback_from_user_id ON session_feedback(from_user_id);
CREATE INDEX IF NOT EXISTS idx_session_feedback_to_user_id ON session_feedback(to_user_id);

-- Индексы для таблицы контента
CREATE INDEX IF NOT EXISTS idx_bot_content_key ON bot_content(content_key);
CREATE INDEX IF NOT EXISTS idx_bot_content_language ON bot_content(language);
CREATE INDEX IF NOT EXISTS idx_bot_content_is_active ON bot_content(is_active);

-- Индексы для таблицы настроек
CREATE INDEX IF NOT EXISTS idx_orator_settings_key ON orator_settings(key);
CREATE INDEX IF NOT EXISTS idx_orator_settings_is_active ON orator_settings(is_active);

-- ============================================================================
-- ТРИГГЕРЫ ДЛЯ ОБНОВЛЕНИЯ TIMESTAMP
-- ============================================================================

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Применение триггеров к таблицам
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_week_registrations_updated_at BEFORE UPDATE ON week_registrations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_pairs_updated_at BEFORE UPDATE ON user_pairs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bot_content_updated_at BEFORE UPDATE ON bot_content
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orator_settings_updated_at BEFORE UPDATE ON orator_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ВСТАВКА БАЗОВОГО КОНТЕНТА
-- ============================================================================

-- Вставка базового контента бота
INSERT INTO bot_content (content_key, content_text, language) VALUES
('welcome_message', 'Привет! Я Alex Orator Bot - ваш помощник для практики ораторского мастерства. Используйте /help для списка команд.', 'ru'),
('help_message', 'Доступные команды:\n/start - Начать работу\n/help - Показать эту справку\n/profile - Ваш профиль\n/register - Зарегистрироваться на неделю\n/topics - Выбрать темы\n/find - Найти партнера\n/pairs - Ваши пары\n/feedback - Оставить отзыв\n/stats - Ваша статистика', 'ru'),
('registration_success', 'Отлично! Вы успешно зарегистрированы на неделю с {start_date} по {end_date}. Время: {time}.', 'ru'),
('no_registration', 'У вас нет активной регистрации на эту неделю. Используйте /register для регистрации.', 'ru'),
('pair_found', 'Найден партнер для практики: {partner_name}. Используйте /pairs для подтверждения.', 'ru'),
('feedback_success', 'Спасибо за отзыв! Ваше мнение поможет улучшить качество занятий.', 'ru')
ON CONFLICT (content_key) DO NOTHING;

-- Вставка базовых настроек
INSERT INTO orator_settings (key, value, description) VALUES
('max_pairs_per_user', '3', 'Максимальное количество пар на пользователя'),
('max_candidates_per_request', '5', 'Максимальное количество кандидатов в ответе'),
('registration_deadline_hours', '24', 'Дедлайн регистрации в часах до начала недели'),
('feedback_required_for_reregistration', 'true', 'Требуется ли отзыв для повторной регистрации'),
('min_feedback_length', '3', 'Минимальная длина отзыва'),
('max_feedback_length', '1000', 'Максимальная длина отзыва'),
('session_duration_minutes', '60', 'Продолжительность занятия в минутах'),
('auto_cancel_pending_pairs_hours', '2', 'Автоматическая отмена неподтвержденных пар через часы')
ON CONFLICT (key) DO NOTHING;

-- Логирование успешной инициализации
DO $$
BEGIN
    RAISE NOTICE 'Alex Orator Bot database initialized successfully';
END $$; 