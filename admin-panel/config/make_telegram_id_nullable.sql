-- Скрипт для изменения поля telegram_id на nullable
-- Это позволит создавать системных администраторов без telegram_id

-- Изменяем поле telegram_id на nullable
ALTER TABLE users ALTER COLUMN telegram_id DROP NOT NULL;

-- Добавляем комментарий к таблице
COMMENT ON COLUMN users.telegram_id IS 'Telegram ID пользователя. NULL для системных администраторов';

-- Уведомление об успешном изменении
DO $$
BEGIN
    RAISE NOTICE '✅ Поле telegram_id успешно изменено на nullable';
    RAISE NOTICE '📋 Теперь можно создавать системных администраторов без telegram_id';
END $$;
