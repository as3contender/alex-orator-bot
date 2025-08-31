import streamlit as st
import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Добавляем путь к корневой директории admin-panel для импорта модулей
current_dir = os.path.dirname(os.path.abspath(__file__))
admin_panel_root = os.path.dirname(current_dir)  # Поднимаемся на уровень выше (из ui/ в admin-panel/)
sys.path.append(admin_panel_root)

try:
    from security.auth import get_auth, auth
    from database.database import get_db, db
except ImportError as e:
    st.error(f"❌ Ошибка импорта модулей: {e}")
    st.error(f"📁 Текущая директория: {os.getcwd()}")
    st.error(f"📁 Путь к admin-panel: {admin_panel_root}")
    st.error(f"📁 Python path: {sys.path}")
    st.stop()


# Настройка страницы
st.set_page_config(
    page_title="Admin Panel - Alex Orator Bot", page_icon="👨🏻‍💼", layout="wide", initial_sidebar_state="expanded"
)

# CSS стили для страницы входа
st.markdown(
    """
<style>


.login-container h2 {
    color: white !important;
    font-size: 2.5rem;
    font-weight: 700;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    margin-bottom: 2rem;
}

.login-container .stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.9);
    border: none;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 16px;
    color: #333;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.login-container .stTextInput > div > div > input:focus {
    background: white;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    transform: translateY(-2px);
    transition: all 0.3s ease;
}

.login-container .stButton > button {
    background: linear-gradient(45deg, #ff6b6b, #ee5a24);
    border: none;
    border-radius: 10px;
    padding: 12px 24px;
    font-size: 18px;
    font-weight: 600;
    color: white;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    transition: all 0.3s ease;
}

.login-container .stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 25px rgba(0, 0, 0, 0.3);
}

.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 80%);
    padding: 2rem;
    border-radius: 15px;
    margin-bottom: 2rem;
    text-align: center;
    color: white;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.main-header h1 {
    color: white !important;
    font-size: 3rem;
    font-weight: 700;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    margin-bottom: 1rem;
}

.main-header p {
    color: rgba(255, 255, 255, 0.9);
    font-size: 1.2rem;
    margin: 0;
}
</style>
""",
    unsafe_allow_html=True,
)

# Инициализация сессии
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "admin_info" not in st.session_state:
    st.session_state.admin_info = None
if "token" not in st.session_state:
    st.session_state.token = None
if "user_role" not in st.session_state:
    st.session_state.user_role = "user"


def login_page():
    """Страница входа"""
    col1, col2, col3 = st.columns(3)
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)

        st.markdown(
            '<h2 style="text-align: center; color: white; margin-bottom: 2rem;">Вход в админ-панель</h2>',
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username = st.text_input("👤 Имя пользователя", key="login_username_input")
            password = st.text_input("🔒 Пароль", type="password", key="login_password_input")

            if st.form_submit_button("🚀 Войти", use_container_width=True):
                if username and password:
                    # Используем новую аутентификацию
                    from security.auth import authenticate_user, get_user_info

                    if authenticate_user(username, password):
                        # Получаем информацию о пользователе
                        user_info = get_user_info(username)
                        if user_info:
                            # Создаем токен (для совместимости)
                            token = auth.create_access_token(data={"sub": user_info["username"]})

                            # Сохраняем в сессии
                            st.session_state.authenticated = True
                            st.session_state.admin_info = user_info
                            st.session_state.token = token

                            # Устанавливаем роль пользователя в session_state для системы прав доступа
                            st.session_state.user_role = user_info.get("role", "user")

                            # Показываем информацию о типе пользователя
                            if user_info.get("user_type") == "admin":
                                st.success("✅ Успешная авторизация администратора!")
                            elif user_info.get("user_type") == "user":
                                st.success("✅ Успешная авторизация пользователя!")
                            else:
                                st.success("✅ Успешная авторизация системного пользователя!")

                            # Принудительно обновляем страницу
                            st.rerun()
                        else:
                            st.error("❌ Ошибка получения информации о пользователе")
                    else:
                        st.error("❌ Неверное имя пользователя или пароль")
                else:
                    st.error("❌ Введите логин и пароль")

        st.markdown("</div>", unsafe_allow_html=True)


def main_admin_page():
    """Основная страница админки"""

    if not st.session_state.authenticated:
        login_page()
        return

    # Проверяем токен (только для администраторов) - временно отключаем для отладки
    # if st.session_state.token and st.session_state.admin_info.get('user_type') == 'admin':
    #     try:
    #         admin_info = auth.get_current_admin(st.session_state.token)
    #         if not admin_info:
    #             st.error("❌ Токен истек. Войдите снова.")
    #             st.session_state.authenticated = False
    #             st.session_state.admin_info = None
    #             st.session_state.token = None
    #             st.rerun()
    #             return
    #     except Exception as e:
    #             st.error(f"❌ Ошибка проверки токена: {e}")
    #             st.session_state.authenticated = False
    #             st.session_state.admin_info = None
    #             st.session_state.token = None
    #             st.rerun()
    #             return

    # Заголовок
    user_type = st.session_state.admin_info.get("user_type", "unknown")
    role_display = st.session_state.admin_info.get("role", "Unknown")

    # Получаем красивую роль для отображения
    from security.auth import get_user_role

    username = st.session_state.admin_info.get("username", "Unknown")
    display_role = get_user_role(username)

    if user_type == "admin":
        header_icon = "👨🏻‍💼"
        header_title = "Админ-панель Alex Orator Bot"
    elif user_type == "user":
        header_icon = "👤"
        header_title = "Панель просмотра Alex Orator Bot"
    else:
        header_icon = "🔧"
        header_title = "Системная панель Alex Orator Bot"

    st.markdown(
        f"""
    <div class="main-header">
        <h1>{header_icon} {header_title}</h1>
        <p>Добро пожаловать, {username} !</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Кнопка выхода
    if st.sidebar.button("🚪 Выйти", type="secondary"):
        st.session_state.authenticated = False
        st.session_state.admin_info = None
        st.session_state.token = None
        st.session_state.user_role = "user"
        st.rerun()

    # Создаем вкладки для разных разделов на основе роли пользователя
    user_role = st.session_state.get("user_role", "user")

    # Определяем доступные вкладки на основе роли
    if user_role in ["super_admin", "admin"]:
        # Администраторы видят управление контентом и пользователями
        tab1, tab2, tab3 = st.tabs(["📝 Управление контентом", "📝 Темы и Задания", "👥 Управление пользователями"])

        with tab1:
            # Основная страница управления контентом
            from content_page import content_management_page

            content_management_page()

        with tab2:
            # Основная страница управления темами и задачами
            from topics_and_tasks_page import topics_and_tasks_management_page

            topics_and_tasks_management_page()

        with tab3:
            # Страница управления пользователями
            from users_management import users_management_page

            users_management_page()

    elif user_role == "moderator":
        # Модераторы видят только управление контентом
        (tab1,) = st.tabs(["📝 Управление контентом"])

        with tab1:
            # Основная страница управления контентом
            from content_page import content_management_page

            content_management_page()

    else:
        # Обычные пользователи видят только просмотр контента
        (tab1,) = st.tabs(["📝 Просмотр контента"])

        with tab1:
            # Только просмотр контента
            from content_page import content_view_page

            content_view_page()


def main():
    """Главная функция"""
    # Проверяем аутентификацию
    if not st.session_state.authenticated:
        login_page()
    else:
        # Проверяем, что у нас есть информация о пользователе
        if st.session_state.admin_info:
            main_admin_page()
        else:
            st.error("❌ Ошибка: информация о пользователе не найдена")
            st.session_state.authenticated = False
            st.session_state.user_role = "user"
            st.rerun()


if __name__ == "__main__":
    main()
