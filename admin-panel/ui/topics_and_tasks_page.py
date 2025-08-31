from database.database import get_db
import streamlit as st
import pandas as pd


def topics_and_tasks_management_page():
    """Главная страница управления темами и задачами"""
    st.header("📝 Управление темами и задачами")

    st.subheader("📝 Управление темами")

    # Показываем таблицу тем
    show_topics_table()

    st.subheader("📝 Добавление новой темы/уровня/задачи")

    add_topic_form()


def add_topic_form():
    """Форма добавления новой темы/уровня/задачи"""
    db = get_db()
    st.subheader("📝 Добавление новой темы/уровня/задачи")

    with st.form("add_topic_form"):
        st.info(
            "💡 **Логика:** Выберите родительский элемент. Если пусто - создается тема (L1), если L1 - создается уровень (L2), если L2 - создается задание (L3)"
        )

        # Получаем все существующие элементы для выбора родителя
        all_elements = get_all_elements_for_parent_selection(db)

        # Добавляем опцию "Нет родителя" для создания корневой темы
        parent_options = ["Нет родителя (создать новую тему)"] + all_elements

        parent_selection = st.selectbox("🏷️ Выберите родительский элемент:", parent_options)

        # Определяем уровень на основе выбранного родителя
        selected_level = determine_level_from_parent(parent_selection)

        # Показываем информацию о том, что будет создано
        if selected_level == 1:
            st.success("🎯 Будет создана новая тема (L1)")
        elif selected_level == 2:
            st.success("🎯 Будет создан новый уровень (L2)")
        else:
            st.success("🎯 Будет создано новое задание (L3)")

        # Поля для ввода
        element_name = st.text_input("📝 Название элемента")
        description = st.text_area("📄 Описание")
        is_active = st.checkbox("✅ Активна", value=True)

        if st.form_submit_button("➕ Добавить элемент"):
            if element_name:
                # Извлекаем название родителя (без ID и эмодзи)
                parent_name = None
                if parent_selection != "Нет родителя (создать новую тему)":
                    # Убираем эмодзи и префикс, оставляем только название
                    if "🏷️ " in parent_selection:
                        # Для тем L1: "🏷️ Название (ID: XX) - Тема L1"
                        parent_name = parent_selection.replace("🏷️ ", "").split(" (ID: ")[0]
                    elif "📚 " in parent_selection:
                        # Для уровней L2: "📚 Название (ID: XX) - Уровень L2"
                        parent_name = parent_selection.replace("📚 ", "").split(" (ID: ")[0]
                    else:
                        # Fallback
                        parent_name = parent_selection.split(" (ID: ")[0] if parent_selection else None

                success = db.add_topic(parent_name, selected_level, element_name, description, is_active)
                if success:
                    st.success(f"✅ Элемент уровня {selected_level} успешно добавлен!")
                    st.rerun()
                else:
                    st.error("❌ Ошибка при добавлении элемента")
            else:
                st.warning("⚠️ Введите название элемента")


def get_existing_topics(db, level: int):
    """Получить список существующих тем или уровней для выбора"""
    try:
        topics_data = db.get_topics_tree()
        if not topics_data:
            return []

        # Фильтруем по уровню
        if level == 1:
            # Получаем уникальные темы (L1) с topic_id
            topics = {}
            for item in topics_data:
                if item.get("topic_name") and item.get("topic_id"):
                    topics[item["topic_name"]] = item["topic_id"]
            # Возвращаем список с topic_id для отображения
            return [f"{name} (ID: {topic_id})" for name, topic_id in sorted(topics.items())]
        elif level == 2:
            # Получаем уникальные уровни (L2) с topic_id
            levels = {}
            for item in topics_data:
                if item.get("level_name") and item.get("topic_id"):
                    levels[item["level_name"]] = item["topic_id"]
            # Возвращаем список с topic_id для отображения
            return [f"{name} (ID: {topic_id})" for name, topic_id in sorted(levels.items())]
        else:
            return []
    except Exception as e:
        st.error(f"❌ Ошибка получения списка тем: {e}")
        return []


def get_all_elements_for_parent_selection(db):
    """Получить все элементы для выбора родителя"""
    try:
        topics_data = db.get_topics_tree()
        if not topics_data:
            return []

        elements = []

        # Добавляем темы (L1)
        topics = {}
        for item in topics_data:
            if item.get("topic_name") and item.get("topic_id"):
                topics[item["topic_name"]] = item["topic_id"]

        for name, topic_id in sorted(topics.items()):
            elements.append(f"🏷️ {name} (ID: {topic_id}) - Тема L1")

        # Добавляем уровни (L2)
        levels = {}
        for item in topics_data:
            if item.get("level_name") and item.get("topic_id"):
                levels[item["level_name"]] = item["topic_id"]

        for name, topic_id in sorted(levels.items()):
            elements.append(f"📚 {name} (ID: {topic_id}) - Уровень L2")

        return elements
    except Exception as e:
        st.error(f"❌ Ошибка получения элементов: {e}")
        return []


def determine_level_from_parent(parent_selection):
    """Определить уровень на основе выбранного родителя"""
    if parent_selection == "Нет родителя (создать новую тему)":
        return 1  # Создаем тему L1
    elif " - Тема L1" in parent_selection:
        return 2  # Создаем уровень L2
    elif " - Уровень L2" in parent_selection:
        return 3  # Создаем задание L3
    else:
        return 1  # По умолчанию создаем тему


def show_topics_table():
    """Показать темы в виде таблицы с колонками Topic (L1), Level (L2), Task (L3)"""

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

        # Получаем все темы из базы данных
    topics_data = db.get_topics_tree()

    if not topics_data:
        st.warning("📝 Темы не найдены")
        return

    # Создаем DataFrame для отображения
    df = pd.DataFrame(topics_data)

    # Переименовываем колонки для лучшего отображения
    df = df.rename(
        columns={
            "topic_id": "🆔 Topic ID",
            "topic_name": "🏷️ Topic (L1)",
            "level_name": "📚 Level (L2)",
            "task_name": "📝 Task (L3)",
            "description": "📄 Описание",
            "is_active": "✅ Активна",
        }
    )

    # Показываем статистику
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        topics_count = len(df[df["🏷️ Topic (L1)"].notna()].drop_duplicates("🏷️ Topic (L1)"))
        st.metric("🏷️ Всего тем", topics_count)

    with col2:
        levels_count = len(df[df["📚 Level (L2)"].notna()].drop_duplicates("📚 Level (L2)"))
        st.metric("📚 Всего уровней", levels_count)

    with col3:
        tasks_count = len(df[df["📝 Task (L3)"].notna()].drop_duplicates("📝 Task (L3)"))
        st.metric("📝 Всего заданий", tasks_count)

    with col4:
        active_count = len(df[df["✅ Активна"] == True])
        st.metric("✅ Активных", active_count)

    # Показываем таблицу
    st.subheader("📊 Таблица тем и заданий")

    # Фильтры
    col1, col2 = st.columns(2)

    with col1:
        # Фильтр по теме
        unique_topics = ["Все"] + df["🏷️ Topic (L1)"].dropna().unique().tolist()
        selected_topic = st.selectbox("🏷️ Фильтр по теме:", unique_topics)

    with col2:
        # Фильтр по активности
        show_active_only = st.checkbox("✅ Показать только активные", value=True)

    # Применяем фильтры
    filtered_df = df.copy()

    if selected_topic != "Все":
        filtered_df = filtered_df[filtered_df["🏷️ Topic (L1)"] == selected_topic]

    if show_active_only:
        filtered_df = filtered_df[filtered_df["✅ Активна"] == True]

    # Показываем отфильтрованную таблицу
    if not filtered_df.empty:
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "✅ Активна": st.column_config.CheckboxColumn(
                    "✅ Активна", help="Статус активности темы/уровня/задания"
                )
            },
        )

        # Экспорт данных
        col1, col2 = st.columns(2)

        with col1:
            csv = filtered_df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📥 Скачать CSV",
                data=csv,
                file_name=f"topics_table_{selected_topic.lower().replace(' ', '_')}.csv",
                mime="text/csv",
            )

        with col2:
            # Показать JSON для отладки
            if st.button("🔍 Показать JSON"):
                st.json(filtered_df.to_dict("records"))
    else:
        st.info("📭 Нет данных для отображения с выбранными фильтрами")
