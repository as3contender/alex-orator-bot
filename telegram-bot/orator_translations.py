"""
Переводы для Alex Orator Bot
"""

TRANSLATIONS = {
    "ru": {
        # Регистрация
        "registration_welcome": "📅 <b>Регистрация на неделю</b>\n\nВыберите предпочтительное время для тренировок:",
        "registration_success": "✅ <b>Регистрация успешна!</b>\n\nТеперь выберите темы для тренировки:",
        "registration_already_exists": "⚠️ У вас уже есть активная регистрация на эту неделю.",
        "registration_cancelled": "❌ Регистрация отменена.",
        "registration_failed": "❌ Ошибка при регистрации. Попробуйте позже.",
        # Темы
        "topics_welcome": "🎯 <b>Выбор тем для тренировки</b>\n\nВыберите темы, которые хотите тренировать:",
        "topics_selected": "✅ <b>Темы выбраны!</b>\n\nТеперь можете найти кандидатов для пары.",
        "topics_failed": "❌ Ошибка при выборе тем. Попробуйте позже.",
        # Поиск кандидатов
        "find_candidates_welcome": "🔍 <b>Поиск кандидатов</b>\n\nИщу подходящих партнеров для тренировки...",
        "find_candidates_success": "✅ <b>Найдено кандидатов: {count}</b>\n\nВыберите партнера:",
        "find_candidates_no_results": "😔 <b>Кандидаты не найдены</b>\n\nПопробуйте позже или измените критерии поиска.",
        "find_candidates_failed": "❌ Ошибка при поиске кандидатов. Попробуйте позже.",
        # Пары
        "pairs_welcome": "👥 Мои пары\n\nВаши текущие и прошлые пары:",
        "pairs_empty": "📭 У вас пока нет пар.\n\nИспользуйте /find для поиска партнеров.",
        "pair_created": "✅ <b>Пара создана!</b>\n\nОжидайте подтверждения от партнера.",
        "pair_confirmed": "✅ <b>Пара подтверждена!</b>\n\nМожете начинать тренировку.",
        "pair_failed": "❌ Ошибка при создании пары. Попробуйте позже.",
        # Обратная связь
        "feedback_welcome": "💬 <b>Обратная связь</b>\n\nВыберите пару для оставления отзыва:",
        "feedback_received": "📥 <b>Полученная обратная связь</b>\n\nОтзывы о ваших выступлениях:",
        "feedback_given": "📤 <b>Данная обратная связь</b>\n\nВаши отзывы о партнерах:",
        "feedback_empty": "📭 Пока нет обратной связи.",
        "feedback_created": "✅ <b>Обратная связь отправлена!</b>\n\nСпасибо за ваш отзыв.",
        # Профиль
        "profile_welcome": "👤 <b>Мой профиль</b>\n\nИнформация о вашем профиле:",
        "profile_updated": "✅ <b>Профиль обновлен!</b>",
        "profile_failed": "❌ Ошибка при обновлении профиля.",
        # Статистика
        "stats_welcome": "📊 <b>Моя статистика</b>\n\nВаши достижения:",
        "stats_format": """📈 <b>Статистика тренировок</b>

🎯 Всего сессий: {total_sessions}
💬 Обратной связи: {feedback_count}
📅 Регистраций: {total_registrations}
👥 Созданных пар: {total_pairs}
✅ Подтвержденных пар: {confirmed_pairs}""",
        # Кнопки
        "button_register": "📅 Зарегистрироваться",
        "button_topics": "🎯 Выбрать темы",
        "button_find": "🔍 Найти кандидатов",
        "button_pairs": "👥 Мои пары",
        "button_feedback": "💬 Обратная связь",
        "button_profile": "👤 Профиль",
        "button_stats": "📊 Статистика",
        "button_help": "❓ Помощь",
        "button_cancel": "❌ Отменить",
        "button_confirm": "✅ Подтвердить",
        "button_back": "⬅️ Назад",
        "button_next": "➡️ Далее",
        # Время
        "time_morning": "🌅 Утро (9:00-12:00)",
        "time_afternoon": "☀️ День (12:00-18:00)",
        "time_evening": "🌆 Вечер (18:00-22:00)",
        # Ошибки
        "error_authentication": "❌ Ошибка аутентификации. Попробуйте /start",
        "error_backend": "❌ Ошибка соединения с сервером. Попробуйте позже.",
        "error_unknown": "❌ Произошла неизвестная ошибка. Попробуйте позже.",
        # Уведомления
        "notification_new_pair": "🎉 <b>Новая пара!</b>\n\nВам предложили создать пару. Используйте /pairs для просмотра.",
        "notification_pair_confirmed": "✅ <b>Пара подтверждена!</b>\n\nМожете начинать тренировку.",
        "notification_reminder": "⏰ <b>Напоминание!</b>\n\nНе забудьте оставить обратную связь после тренировки.",
        # Язык
        "language_changed": "🌐 Язык изменен на русский.",
    },
}


def get_text(key: str, language: str = "ru") -> str:
    """Получить текст по ключу и языку"""
    return TRANSLATIONS.get(language, TRANSLATIONS["ru"]).get(key, f"[{key}]")


def get_button_text(key: str, language: str = "ru") -> str:
    """Получить текст кнопки по ключу и языку"""
    return get_text(f"button_{key}", language)
