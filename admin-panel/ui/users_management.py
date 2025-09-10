#!/usr/bin/env python3

import streamlit as st
import pandas as pd
from database.database import get_db
from datetime import datetime
import uuid
from security.access_control import get_user_permissions, check_permission, show_access_denied


def users_management_page():
    """Страница управления пользователями"""
    st.header("👥 Управление пользователями")
    
    # Проверяем права доступа
    user_role = st.session_state.get("user_role", "user")
    permissions = get_user_permissions(user_role)
    
    if not permissions["can_manage_users"]:
        show_access_denied("У вас нет прав для управления пользователями")
        st.info("💡 Для доступа к этой странице требуется роль администратора или модератора")
        return
    
    # Показываем информацию о правах пользователя
    st.info(f"🔒 Ваша роль: {permissions['name']}")
    
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
    
    # Создаем две колонки
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📋 Список пользователей из БД")
        
        try:
            # Получаем всех пользователей
            users = db.get_all_users()
            
            if users:
                # Создаем DataFrame для отображения
                df_data = []
                for user in users:
                    # Формируем полное имя из first_name и last_name
                    first_name = user.get('first_name', '')
                    last_name = user.get('last_name', '')
                    full_name = f"{first_name} {last_name}".strip() if first_name or last_name else 'N/A'
                    
                    # Получаем роль пользователя
                    user_role = user.get('role', 'user')
                    role_display = {
                        'user': '👤 Пользователь',
                        'admin': '👨🏻‍💼 Администратор',
                        'moderator': '🛡️ Модератор',
                        'super_admin': '👑 Супер-администратор'
                    }.get(user_role, f'❓ {user_role}')
                    
                    df_data.append({
                        "ID": user.get('id', ''),
                        "telegram_id": user.get('telegram_id', ''),
                        "username": user.get('username', 'N/A'),
                        "email": user.get('email'),
                        "full_name": full_name,
                        "Роль": role_display,
                        "is_active": user.get('is_active', False),
                        "created_at": user.get('created_at', 'N/A'),
                        "updated_at": user.get('updated_at', 'N/A')
                    })
                
                # Создаем DataFrame
                df = pd.DataFrame(df_data)
                
                # Отображаем таблицу
                st.dataframe(df, use_container_width=True)
                
                # Показываем общее количество пользователей
                st.info(f"📊 Всего пользователей: {len(users)}")
                
                # Статистика по ролям
                role_counts = {}
                for user in users:
                    role = user.get('role', 'user')
                    role_counts[role] = role_counts.get(role, 0) + 1
                
                # Показываем статистику по ролям
                st.subheader("🎭 Распределение по ролям")
                role_cols = st.columns(len(role_counts))
                
                for i, (role, count) in enumerate(role_counts.items()):
                    with role_cols[i]:
                        role_icon = {
                            'user': '👤',
                            'admin': '👨🏻‍💼',
                            'moderator': '🛡️',
                            'super_admin': '👑'
                        }.get(role, '❓')
                        
                        role_name = {
                            'user': 'Пользователи',
                            'admin': 'Администраторы',
                            'moderator': 'Модераторы',
                            'super_admin': 'Супер-администраторы'
                        }.get(role, role.capitalize())
                        
                        st.metric(f"{role_icon} {role_name}", count)
                
                # Кнопка обновления
                if st.button("🔄 Обновить", key="refresh_users"):
                    st.rerun()
                
                # Раздел удаления пользователей (только для администраторов)
                if permissions["can_delete"]:
                    st.subheader("🗑️ Удаление пользователя")
                    st.warning("⚠️ Внимание: Удаление пользователя необратимо!")
                    
                    # Выбор пользователя для удаления
                    user_options = []
                    for user in users:
                        username = user.get('username', 'N/A') or 'Без username'
                        user_id = user.get('id', '')
                        user_options.append((user_id, f"{username} (ID: {user_id[:8]}...)"))
                    
                    if user_options:
                        selected_user_id = st.selectbox(
                            "👤 Выберите пользователя для удаления:",
                            options=[opt[0] for opt in user_options],
                            format_func=lambda x: next(opt[1] for opt in user_options if opt[0] == x),
                            key="delete_user_select"
                        )
                        
                        # Показываем информацию о выбранном пользователе
                        selected_user = next(user for user in users if user.get('id') == selected_user_id)
                        if selected_user:
                            username = selected_user.get('username', 'N/A') or 'Без username'
                            telegram_id = selected_user.get('telegram_id', 'N/A')
                            full_name = f"{selected_user.get('first_name', '')} {selected_user.get('last_name', '')}".strip()
                            
                            # Кнопка удаления пользователя
                            if st.button("🗑️ Удалить пользователя", key="delete_selected_user", type="primary"):
                                if db.delete_user(selected_user_id):
                                    st.success(f"✅ Пользователь {username} успешно удален!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Ошибка удаления пользователя {username}")
                    else:
                        st.info("📝 Нет пользователей для удаления")
                else:
                    st.info("ℹ️ Удаление пользователей доступно только администраторам")
                    
            else:
                st.info("📝 Пользователи не найдены")
                
        except Exception as e:
            st.error(f"❌ Ошибка загрузки пользователей: {e}")
    
    with col2:
        st.subheader("➕ Добавить нового пользователя")
        
        with st.form("add_user_form"):
            # Обязательные поля
            username = st.text_input("👤 Имя пользователя*", key="new_username")
            password = st.text_input("🔒 Пароль*", type="password", key="new_password")
            
            # Дополнительные поля
            role_display = st.selectbox(
                "👥 Роль",
                options=["Пользователь", "Администратор", "Модератор"],
                index=0,
                key="new_role"
            )
            
            # Преобразуем отображаемую роль в значение для БД
            role_mapping = {
                "Пользователь": "user",
                "Администратор": "admin", 
                "Модератор": "moderator"
            }
            role = role_mapping[role_display]
            
            full_name = st.text_input("👤 Полное имя", key="new_full_name")
            email = st.text_input("📧 Email", key="new_email")
            telegram_id = st.text_input("📱 Telegram ID", key="new_telegram_id")
            
            # Кнопка добавления
            if st.form_submit_button("➕ Добавить пользователя", use_container_width=True):
                if username and password:
                    try:
                        # Показываем отладочную информацию
                        st.info(f"🔍 Создаем пользователя с ролью: {role_display} ({role})")
                        
                        # Создаем нового пользователя
                        success = db.create_user(
                            username=username,
                            password=password,
                            role=role,  # Передаем выбранную роль
                            full_name=full_name if full_name else None,
                            email=email if email else None,
                            telegram_id=telegram_id if telegram_id else None
                        )
                        
                        if success:
                            st.success(f"✅ Пользователь {username} с ролью '{role_display}' успешно добавлен!")
                            st.rerun()
                        else:
                            st.error("❌ Ошибка добавления пользователя")
                            st.info("💡 Проверьте логи в терминале для деталей ошибки")
                    except Exception as e:
                        st.error(f"❌ Ошибка: {e}")
                        st.info("💡 Детали ошибки записаны в логи терминала")
                else:
                    st.error("❌ Заполните обязательные поля (имя пользователя и пароль)")


if __name__ == "__main__":
    users_management_page()
