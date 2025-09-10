#!/usr/bin/env python3

import streamlit as st
import pandas as pd
import os
import io
from database.database import get_db
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger


def content_view_page():
    """Страница просмотра контента (только чтение)"""
    st.header("📝 Просмотр контента")
    st.info("🔍 Режим просмотра - редактирование недоступно")

    # Получаем экземпляр базы данных
    db = get_db()

    # Проверяем подключение к базе данных
    try:
        # Загружаем контент
        content_list = db.get_all_bot_content()

        if content_list:
            # Фильтры
            col1, col2 = st.columns([3, 1])

            with col1:
                # Получаем уникальные ключи контента для фильтра
                content_keys = ["Все"] + sorted(list(set(item["content_key"] for item in content_list)))
                content_key_filter = st.selectbox(
                    "Фильтр по ключу контента",
                    content_keys,
                    key="content_key_filter_view",
                    help="Выберите ключ контента для фильтрации",
                )

            with col2:
                if st.button("🔄 Обновить", key="refresh_btn_view"):
                    st.rerun()

            # Применяем фильтры
            filtered_content = content_list

            if content_key_filter and content_key_filter != "Все":
                filtered_content = [item for item in filtered_content if item["content_key"] == content_key_filter]

            # Отображаем отфильтрованный контент
            if filtered_content:
                # Создаем DataFrame для отображения
                df_data = []
                for item in filtered_content:
                    # Ограничиваем текст до 30 символов
                    content_preview = (
                        item["content_text"][:30] + "..." if len(item["content_text"]) > 30 else item["content_text"]
                    )

                    df_data.append(
                        {
                            "Ключ": item["content_key"],
                            "Текст (30 символов)": content_preview,
                            "Создан": item["created_at"].strftime("%Y-%m-%d %H:%M") if item["created_at"] else "N/A",
                            "Обновлен": item["updated_at"].strftime("%Y-%m-%d %H:%M") if item["updated_at"] else "N/A",
                        }
                    )

                # Отображаем таблицу
                st.dataframe(df_data, use_container_width=True)

                # Показываем общее количество
                st.info(f"📊 Всего записей: {len(filtered_content)}")
            else:
                st.info("📝 Нет контента для отображения с выбранными фильтрами")
        else:
            st.warning("⚠️ Нет данных для отображения")
    except Exception as e:
        st.error(f"❌ Ошибка загрузки: {e}")
        st.info("💡 Проверьте логи для получения дополнительной информации")


def content_management_page():
    """Главная страница управления контентом"""

    # Создаем вкладки
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Просмотр", "➕ Создать", "✏️ Редактировать", "📊 Статистика"])

    with tab1:
        view_content_tab()

    with tab2:
        create_content_tab()

    with tab3:
        edit_content_tab()

    with tab4:
        content_stats_tab()


def view_content_tab():
    """Вкладка просмотра контента"""
    st.subheader("📋 Просмотр контента")

    # Получаем экземпляр базы данных
    db = get_db()

    # Проверяем подключение к базе данных
    try:
        # Загружаем контент
        content_list = db.get_all_bot_content()

        if content_list:
            # Фильтры
            col1, col2 = st.columns([3, 1])

            with col1:
                # Получаем уникальные ключи контента для фильтра
                content_keys = ["Все"] + sorted(list(set(item["content_key"] for item in content_list)))
                content_key_filter = st.selectbox(
                    "Фильтр по ключу контента",
                    content_keys,
                    key="content_key_filter",
                    help="Выберите ключ контента для фильтрации",
                )

            with col2:
                col2_1, col2_2 = st.columns(2)

                with col2_1:
                    if st.button("🔄 Обновить", key="refresh_btn"):
                        st.rerun()

                with col2_2:
                    if st.button("📥 Скачать CSV", key="download_csv_btn"):
                        download_csv(filtered_content)

            # Применяем фильтры
            filtered_content = content_list

            if content_key_filter and content_key_filter != "Все":
                filtered_content = [item for item in filtered_content if item["content_key"] == content_key_filter]

            # Отображаем отфильтрованный контент
            if filtered_content:
                # Создаем DataFrame для отображения
                df_data = []
                for item in filtered_content:
                    # Ограничиваем текст до 30 символов
                    content_preview = (
                        item["content_text"][:30] + "..." if len(item["content_text"]) > 30 else item["content_text"]
                    )

                    df_data.append(
                        {
                            "Ключ": item["content_key"],
                            "Текст (30 символов)": content_preview,
                            "Создан": item["created_at"].strftime("%Y-%m-%d %H:%M") if item["created_at"] else "N/A",
                            "Обновлен": item["updated_at"].strftime("%Y-%m-%d %H:%M") if item["updated_at"] else "N/A",
                        }
                    )

                # Отображаем таблицу
                st.dataframe(df_data, use_container_width=True)
            else:
                st.info("📝 Нет контента для отображения с выбранными фильтрами")
        else:
            st.warning("⚠️ Нет данных для отображения")
    except Exception as e:
        st.error(f"❌ Ошибка загрузки: {e}")
        st.info("💡 Проверьте логи для получения дополнительной информации")


def create_content_tab():
    """Вкладка создания нового контента"""
    st.subheader("➕ Создать новый контент")

    # Получаем экземпляр базы данных
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

    with st.form("create_content_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            content_key = st.text_input(
                "🔑 Ключ контента*",
                placeholder="например: welcome_message",
                help="Уникальный идентификатор для контента",
            )
            language = st.selectbox("🌐 Язык*", ["ru", "en", "kz"], index=0, help="Язык контента")

        with col2:
            is_active = st.checkbox("✅ Активен", value=True, help="Будет ли контент доступен боту")

        content_text = st.text_area(
            "📄 Текст контента*", height=200, placeholder="Введите текст контента...", help="Основной текст контента"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.form_submit_button("💾 Создать", type="primary"):
                if content_key and content_text:
                    if db.create_bot_content(content_key, content_text, language, is_active):
                        st.success("✅ Контент успешно создан!")
                        st.rerun()
                    else:
                        st.error("❌ Ошибка создания контента")
                else:
                    st.error("❌ Заполните все обязательные поля")

        with col2:
            if st.form_submit_button("❌ Отмена"):
                st.rerun()


def edit_content_tab():
    """Вкладка редактирования контента"""
    st.subheader("✏️ Редактирование контента")

    # Получаем экземпляр базы данных
    db = get_db()

    # Функциональность редактирования контента
    st.subheader("📝 Редактирование контента")

    # Загружаем весь контент для выбора
    try:
        content_list = db.get_all_bot_content()

        if content_list:
            # Выбор контента для редактирования
            st.write("**Выберите контент для редактирования:**")

            # Создаем список для выбора
            content_options = [f"{item['content_key']} ({item['language']})" for item in content_list]
            content_indices = list(range(len(content_list)))

            selected_index = st.selectbox(
                "Контент:",
                content_indices,
                format_func=lambda x: content_options[x],
                key="edit_content_select",
                help="Выберите контент для редактирования",
            )

            if selected_index is not None:
                selected_item = content_list[selected_index]

                st.write(f"**✏️ Редактирование:** {selected_item['content_key']} ({selected_item['language']})")

                with st.form("edit_content_form"):
                    col1, col2 = st.columns(2)

                    with col1:
                        new_text = st.text_area(
                            "📄 Новый текст*",
                            value=selected_item["content_text"],
                            height=200,
                            key="edit_text",
                            help="Отредактируйте текст контента",
                        )

                    with col2:
                        st.write("**📊 Информация:**")
                        st.write(f"**Ключ:** {selected_item['content_key']}")
                        st.write(f"**Язык:** {selected_item['language']}")
                        st.write(f"**Статус:** {'🟢 Активен' if selected_item['is_active'] else '🔴 Неактивен'}")
                        st.write(f"**Создан:** {selected_item['created_at']}")
                        st.write(f"**Обновлен:** {selected_item['updated_at']}")

                        # Предварительный просмотр
                        if new_text and new_text != selected_item["content_text"]:
                            st.markdown("**👀 Предварительный просмотр:**")
                            st.info(new_text)

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.form_submit_button("💾 Сохранить", type="primary"):
                            if new_text and new_text != selected_item["content_text"]:
                                if db.update_bot_content(
                                    selected_item["content_key"], new_text, selected_item["language"]
                                ):
                                    st.success("✅ Контент успешно обновлен!")
                                    st.rerun()
                                else:
                                    st.error("❌ Ошибка обновления контента")
                            elif new_text == selected_item["content_text"]:
                                st.info("ℹ️ Текст не изменился")
                            else:
                                st.error("❌ Введите текст")

                    with col2:
                        if st.form_submit_button("❌ Отмена"):
                            st.rerun()

                    with col3:
                        if st.form_submit_button("🗑️ Удалить навсегда", type="secondary"):
                            # Подтверждение полного удаления
                            st.warning("⚠️ ВНИМАНИЕ: Это действие полностью удалит контент из базы данных!")
                            if st.checkbox("Подтверждаю полное удаление", key="confirm_permanent_delete"):
                                if db.permanently_delete_bot_content(
                                    selected_item["content_key"], selected_item["language"]
                                ):
                                    st.success("✅ Контент полностью удален из базы данных!")
                                    st.rerun()
                                else:
                                    st.error("❌ Ошибка полного удаления контента")
                            else:
                                st.info("ℹ️ Поставьте галочку для подтверждения полного удаления")
        else:
            st.info("📭 Нет доступного контента для редактирования")

    except Exception as e:
        st.error(f"❌ Ошибка загрузки контента: {e}")
        st.info("💡 Проверьте подключение к базе данных")


def content_stats_tab():
    """Вкладка статистики контента"""
    st.subheader("📊 Статистика")

    logger.debug("content_stats_tab")

    # Получаем экземпляр базы данных
    db = get_db()

    try:
        # Проверяем подключение к базе данных
        if not db.conn:
            st.warning("⚠️ Нет подключения к базе данных. Попытка подключения...")
            db.connect()
            st.success("✅ Подключение к базе данных установлено!")

        # Выполнение и отображение результатов из backend/services/statistics.sql
        try:
            # путь относительно admin_panel: подняться на уровень вверх и перейти к backend/services/statistics.sql
            sql_results = db.get_statistics()
            logger.info(f"sql_results: {sql_results}")

            if sql_results:
                # Создаем DataFrame для отображения
                df_sql = pd.DataFrame(sql_results)

                # Переименовываем колонки для лучшего понимания
                df_sql.columns = [
                    "Дата",
                    "Новые пользователи",
                    "Регистрации на неделю",
                    "Новые пары",
                    "Подтвержденные пары",
                ]

                # Отображаем данные
                st.dataframe(df_sql, use_container_width=True)

                # Добавляем графики
                st.subheader("📈 Графики статистики")

                col1, col2 = st.columns(2)

                with col1:
                    # График новых пользователей
                    if "Новые пользователи" in df_sql.columns:
                        st.line_chart(df_sql.set_index("Дата")["Новые пользователи"])
                        st.caption("Новые пользователи по дням")

                with col2:
                    # График регистраций на неделю
                    if "Регистрации на неделю" in df_sql.columns:
                        st.line_chart(df_sql.set_index("Дата")["Регистрации на неделю"])
                        st.caption("Регистрации на неделю по дням")

                # График пар
                col3, col4 = st.columns(2)

                with col3:
                    if "Новые пары" in df_sql.columns:
                        st.line_chart(df_sql.set_index("Дата")["Новые пары"])
                        st.caption("Новые пары по дням")

                with col4:
                    if "Подтвержденные пары" in df_sql.columns:
                        st.line_chart(df_sql.set_index("Дата")["Подтвержденные пары"])
                        st.caption("Подтвержденные пары по дням")

                # Сводная статистика
                st.subheader("📊 Сводная статистика")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    total_users = df_sql["Новые пользователи"].sum()
                    st.metric("👥 Всего новых пользователей", total_users)

                with col2:
                    total_registrations = df_sql["Регистрации на неделю"].sum()
                    st.metric("📅 Всего регистраций", total_registrations)

                with col3:
                    total_pairs = df_sql["Новые пары"].sum()
                    st.metric("🤝 Всего новых пар", total_pairs)

                with col4:
                    total_confirmed = df_sql["Подтвержденные пары"].sum()
                    st.metric("✅ Всего подтвержденных пар", total_confirmed)

            else:
                st.info("Нет данных из statistics.sql или запрос не вернул строк")
        except Exception as e:
            st.error(f"❌ Ошибка выполнения statistics.sql: {e}")
            st.info("💡 Проверьте путь к файлу и подключение к базе данных")

    except Exception as e:
        st.error(f"❌ Ошибка подключения к базе данных: {e}")
        st.info("💡 Убедитесь, что Docker контейнеры запущены и база данных доступна")


def download_csv(content_list):
    """Функция для скачивания данных в CSV формате"""
    try:
        if not content_list:
            st.warning("⚠️ Нет данных для скачивания")
            return

        # Создаем DataFrame для экспорта
        export_data = []
        for item in content_list:
            export_data.append(
                {
                    "Ключ контента": item["content_key"],
                    "Полный текст": item["content_text"],
                    "Язык": item["language"],
                    "Статус": "Активен" if item["is_active"] else "Неактивен",
                    "Дата создания": item["created_at"].strftime("%Y-%m-%d %H:%M:%S") if item["created_at"] else "N/A",
                    "Дата обновления": (
                        item["updated_at"].strftime("%Y-%m-%d %H:%M:%S") if item["updated_at"] else "N/A"
                    ),
                    "ID": str(item["id"]) if "id" in item else "N/A",
                }
            )

        # Создаем DataFrame
        df_export = pd.DataFrame(export_data)

        # Создаем CSV в памяти
        csv_buffer = io.StringIO()
        df_export.to_csv(
            csv_buffer, index=False, encoding="utf-8-sig"
        )  # utf-8-sig для корректного отображения кириллицы в Excel
        csv_data = csv_buffer.getvalue()

        # Генерируем имя файла с текущей датой
        current_date = datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"bot_content_export_{current_date}.csv"

        # Создаем кнопку для скачивания
        st.download_button(
            label="📥 Скачать CSV файл", data=csv_data, file_name=filename, mime="text/csv", key="download_csv_file"
        )

        # Показываем информацию о файле
        st.success(f"✅ Файл готов к скачиванию: {filename}")
        st.info(f"📊 Экспортировано записей: {len(export_data)}")

        # Показываем предварительный просмотр данных
        with st.expander("👀 Предварительный просмотр экспортируемых данных", expanded=False):
            st.dataframe(df_export, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Ошибка создания CSV файла: {e}")
        st.info("💡 Проверьте данные и попробуйте снова")


if __name__ == "__main__":
    content_management_page()
