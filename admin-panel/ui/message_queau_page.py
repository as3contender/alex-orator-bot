from database.database import get_db
import streamlit as st
import pandas as pd
import json


def message_queue_management_page():
    """Главная страница управления очередью сообщений"""
    st.header("📨 Управление очередью сообщений")

    st.subheader("📊 Таблица сообщений в очереди")

    # Показываем таблицу сообщений
    show_message_queue_table()

    st.subheader("📝 Добавление нового сообщения")

    # Показываем форму добавления
    add_message_form()


def show_message_queue_table():
    """Показать таблицу сообщений в очереди"""
    db = get_db()

    # Проверяем подключение к базе данных
    if not db.conn:
        st.warning("⚠️ Нет подключения к базе данных. Попытка подключения...")
        try:
            db.connect()
            st.success("✅ Подключение к базе данных установлено!")
        except Exception as e:
            st.error(f"❌ Не удалось подключиться к базе данных: {e}")
            st.info("💡 Убедитесь, что Docker контейнеры запущены и база данных доступна")
            return

    # Получаем сообщения из очереди
    messages_data = db.get_message_queue()

    if not messages_data:
        st.warning("📭 Сообщений в очереди не найдено")
        return

    # Создаем DataFrame для отображения
    df = pd.DataFrame(messages_data)

    # Переименовываем колонки для лучшего отображения
    df = df.rename(
        columns={
            "id": "🆔 ID",
            "user_id": "👤 User ID",
            "message": "💬 Сообщение",
            "keyboard": "⌨️ Клавиатура",
            "sent": "✅ Отправлено",
            "created_at": "📅 Создано",
            "sent_at": "📤 Отправлено в",
        }
    )

    # Показываем статистику
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_count = len(df)
        st.metric("📨 Всего сообщений", total_count)

    with col2:
        sent_count = len(df[df["✅ Отправлено"] == True])
        st.metric("📤 Отправлено", sent_count)

    with col3:
        pending_count = len(df[df["✅ Отправлено"] == False])
        st.metric("⏳ В очереди", pending_count)

    with col4:
        unique_users = len(df["👤 User ID"].unique())
        st.metric("👥 Уникальных пользователей", unique_users)

    # Показываем таблицу
    st.subheader("📊 Таблица сообщений")

    # Фильтры
    col1, col2 = st.columns(2)

    with col1:
        # Фильтр по статусу отправки
        status_filter = st.selectbox("📤 Фильтр по статусу:", ["Все", "Отправлено", "В очереди"])

    with col2:
        # Фильтр по пользователю
        unique_users_list = ["Все"] + df["👤 User ID"].unique().tolist()
        user_filter = st.selectbox("👤 Фильтр по пользователю:", unique_users_list)

    # Применяем фильтры
    filtered_df = df.copy()

    if status_filter == "Отправлено":
        filtered_df = filtered_df[filtered_df["✅ Отправлено"] == True]
    elif status_filter == "В очереди":
        filtered_df = filtered_df[filtered_df["✅ Отправлено"] == False]

    if user_filter != "Все":
        filtered_df = filtered_df[filtered_df["👤 User ID"] == user_filter]

    # Показываем отфильтрованную таблицу
    if not filtered_df.empty:
        # Ограничиваем длину сообщения для отображения
        display_df = filtered_df.copy()
        display_df["💬 Сообщение"] = display_df["💬 Сообщение"].apply(
            lambda x: x[:100] + "..." if len(str(x)) > 100 else x
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "✅ Отправлено": st.column_config.CheckboxColumn("✅ Отправлено", help="Статус отправки сообщения"),
                "💬 Сообщение": st.column_config.TextColumn(
                    "💬 Сообщение", help="Текст сообщения (обрезано для отображения)"
                ),
                "⌨️ Клавиатура": st.column_config.TextColumn("⌨️ Клавиатура", help="JSON структура клавиатуры"),
            },
        )

        # Экспорт данных
        col1, col2 = st.columns(2)

        with col1:
            csv = filtered_df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 Скачать CSV",
                data=csv,
                file_name=f"message_queue_{status_filter.lower().replace(' ', '_')}.csv",
                mime="text/csv",
            )

        with col2:
            # Показать JSON для отладки
            if st.button("🔍 Показать JSON", key="show_json_messages"):
                st.json(filtered_df.to_dict("records"))
    else:
        st.info("📭 Нет данных для отображения с выбранными фильтрами")


def add_message_form():
    """Форма добавления нового сообщения"""
    db = get_db()

    st.info(
        "💡 **Логика:** Выберите тип получателей и введите сообщение. Сообщение будет добавлено в очередь для отправки."
    )

    with st.form("add_message_form"):
        # Выбор типа получателей
        recipient_type = st.selectbox(
            "👥 Тип получателей:",
            ["single_user", "week_registration_users", "active_users"],
            format_func=lambda x: {
                "single_user": "👤 Конкретный пользователь",
                "week_registration_users": "📅 Зарегистрированные на неделю",
                "active_users": "✅ Все активные пользователи",
            }[x],
        )

        # Дополнительные поля в зависимости от типа получателей
        selected_user = None
        if recipient_type == "single_user":
            users = get_users_for_selection(db)
            if users:
                user_options = [
                    f"{user['first_name']} {user['last_name']} (@{user['username']}) - {user['telegram_id']}"
                    for user in users
                ]
                selected_user_full = st.selectbox("👤 Выберите пользователя:", user_options)
                if selected_user_full:
                    # Извлекаем telegram_id из выбранной строки
                    selected_user = selected_user_full.split(" - ")[-1]
            else:
                st.warning("⚠️ Нет доступных пользователей с telegram_id")

        # Поле для сообщения
        message_text = st.text_area("💬 Текст сообщения:", placeholder="Введите текст сообщения...", height=150)

        # Поле для клавиатуры (опционально)
        keyboard_json = st.text_area(
            "⌨️ Клавиатура (JSON, опционально):",
            placeholder='{"inline_keyboard": [{"text": "Кнопка", "callback_data": "action"}]]}',
            height=100,
            help="JSON структура клавиатуры Telegram. Оставьте пустым, если клавиатура не нужна.",
        )

        # Предварительный просмотр
        if message_text:
            st.subheader("👀 Предварительный просмотр:")
            st.info(f"**Получатели:** {get_recipient_description(recipient_type, selected_user)}")
            st.write(f"**Сообщение:** {message_text}")
            if keyboard_json:
                try:
                    keyboard_data = json.loads(keyboard_json)
                    st.write(f"**Клавиатура:** {json.dumps(keyboard_data, indent=2, ensure_ascii=False)}")
                except json.JSONDecodeError:
                    st.error("❌ Ошибка в JSON формате клавиатуры")

        if st.form_submit_button("📨 Добавить сообщение(я) в очередь"):
            if message_text:
                # Парсим клавиатуру
                keyboard_data = None
                if keyboard_json:
                    try:
                        keyboard_data = json.loads(keyboard_json)
                    except json.JSONDecodeError:
                        st.error("❌ Ошибка в JSON формате клавиатуры")
                        return

                # Получаем список пользователей для отправки
                user_ids = get_user_ids_for_sending(db, recipient_type, selected_user)

                if not user_ids:
                    st.warning("⚠️ Нет пользователей для отправки сообщения")
                    return

                # Добавляем сообщения в очередь
                success_count = 0
                error_count = 0

                for user_id in user_ids:
                    success = db.add_message_to_queue(user_id, message_text, keyboard_data)
                    if success:
                        success_count += 1
                    else:
                        error_count += 1

                if success_count > 0:
                    st.success(f"✅ Успешно добавлено {success_count} сообщений в очередь!")
                    if error_count > 0:
                        st.warning(f"⚠️ Не удалось добавить {error_count} сообщений")
                    st.rerun()
                else:
                    st.error("❌ Не удалось добавить ни одного сообщения в очередь")
            else:
                st.warning("⚠️ Введите текст сообщения")


def get_users_for_selection(db):
    """Получить пользователей для выбора в форме"""
    try:
        return db.get_users_by_telegram_id()
    except Exception as e:
        st.error(f"❌ Ошибка получения пользователей: {e}")
        return []


def get_recipient_description(recipient_type, selected_user=None):
    """Получить описание получателей"""
    descriptions = {
        "single_user": (
            f"Конкретный пользователь: {selected_user}" if selected_user else "Конкретный пользователь (не выбран)"
        ),
        "week_registration_users": "Все пользователи, зарегистрированные на текущую неделю",
        "active_users": "Все активные пользователи с telegram_id",
    }
    return descriptions.get(recipient_type, "Неизвестный тип")


def get_user_ids_for_sending(db, recipient_type, selected_user=None):
    """Получить список user_id для отправки сообщений"""
    user_ids = []

    try:
        if recipient_type == "single_user" and selected_user:
            user_ids = [selected_user]
        elif recipient_type == "week_registration_users":
            users = db.get_week_registration_users()
            if users:  # Проверяем, что users не None и не пустой
                user_ids = [user["user_id"] for user in users]
            else:
                st.warning("⚠️ Нет пользователей, зарегистрированных на неделю")
        elif recipient_type == "active_users":
            users = db.get_active_users()
            if users:  # Проверяем, что users не None и не пустой
                user_ids = [user["user_id"] for user in users]
            else:
                st.warning("⚠️ Нет активных пользователей")

        return user_ids
    except Exception as e:
        st.error(f"❌ Ошибка получения списка пользователей: {e}")
        return []
