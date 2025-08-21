#!/usr/bin/env python3
"""
Модуль для управления правами доступа на основе ролей пользователей
"""

import streamlit as st
from typing import Dict, List, Any, Optional

# Определяем права доступа для каждой роли
ROLE_PERMISSIONS = {
    "super_admin": {
        "name": "👑 Супер-администратор",
        "can_view": True,
        "can_edit": True,
        "can_delete": True,
        "can_create": True,
        "can_manage_users": True,
        "can_manage_content": True,
        "can_access_admin_panel": True,
        "can_manage_roles": True
    },
    "admin": {
        "name": "👨🏻‍💼 Администратор",
        "can_view": True,
        "can_edit": True,
        "can_delete": True,
        "can_create": True,
        "can_manage_users": True,
        "can_manage_content": True,
        "can_access_admin_panel": True,
        "can_manage_roles": False
    },
    "moderator": {
        "name": "🛡️ Модератор",
        "can_view": True,
        "can_edit": True,
        "can_delete": False,  # Модераторы не могут удалять
        "can_create": True,
        "can_manage_users": False,  # Модераторы не могут управлять пользователями
        "can_manage_content": True,
        "can_access_admin_panel": True,
        "can_manage_roles": False
    },
    "user": {
        "name": "👤 Пользователь",
        "can_view": True,
        "can_edit": False,
        "can_delete": False,
        "can_create": False,
        "can_manage_users": False,
        "can_manage_content": False,
        "can_access_admin_panel": False,  # Обычные пользователи не могут заходить в админ-панель
        "can_manage_roles": False
    }
}

def get_user_permissions(user_role: str) -> Dict[str, Any]:
    """
    Получить права доступа для роли пользователя
    
    Args:
        user_role: Роль пользователя (super_admin, admin, moderator, user)
        
    Returns:
        Словарь с правами доступа
    """
    return ROLE_PERMISSIONS.get(user_role, ROLE_PERMISSIONS["user"])

def check_permission(user_role: str, permission: str) -> bool:
    """
    Проверить, есть ли у пользователя определенное право
    
    Args:
        user_role: Роль пользователя
        permission: Название права для проверки
        
    Returns:
        True если есть право, False если нет
    """
    permissions = get_user_permissions(user_role)
    return permissions.get(permission, False)

def require_permission(permission: str):
    """
    Декоратор для проверки прав доступа к функции
    
    Args:
        permission: Название права для проверки
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Получаем роль пользователя из session_state
            user_role = st.session_state.get("user_role", "user")
            
            if check_permission(user_role, permission):
                return func(*args, **kwargs)
            else:
                st.error("❌ У вас нет прав для выполнения этого действия")
                st.info(f"💡 Требуется роль с правами: {permission}")
                return None
        return wrapper
    return decorator

def show_access_denied(message: str = "У вас нет прав для выполнения этого действия"):
    """
    Показать сообщение об отказе в доступе
    
    Args:
        message: Сообщение об ошибке
    """
    st.error(f"❌ {message}")
    st.info("💡 Обратитесь к администратору для получения дополнительных прав")

def can_access_page(user_role: str, page_type: str) -> bool:
    """
    Проверить, может ли пользователь с данной ролью получить доступ к странице
    
    Args:
        user_role: Роль пользователя
        page_type: Тип страницы (admin, moderator, user)
        
    Returns:
        True если доступ разрешен, False если запрещен
    """
    if page_type == "admin":
        return user_role in ["super_admin", "admin"]
    elif page_type == "moderator":
        return user_role in ["super_admin", "admin", "moderator"]
    elif page_type == "user":
        return True  # Все роли могут просматривать
    else:
        return False

def get_accessible_pages(user_role: str) -> List[str]:
    """
    Получить список доступных страниц для роли пользователя
    
    Args:
        user_role: Роль пользователя
        
    Returns:
        Список доступных страниц
    """
    permissions = get_user_permissions(user_role)
    
    accessible_pages = []
    
    if permissions["can_manage_users"]:
        accessible_pages.append("👥 Управление пользователями")
    
    if permissions["can_manage_content"]:
        accessible_pages.append("📝 Управление контентом")
    
    # Просмотр пользователей доступен всем
    accessible_pages.append("👤 Просмотр пользователей")
    
    return accessible_pages

def show_user_permissions_info(user_role: str):
    """
    Показать информацию о правах пользователя
    
    Args:
        user_role: Роль пользователя
    """
    permissions = get_user_permissions(user_role)
    
    st.subheader(f"🔒 Ваши права доступа: {permissions['name']}")
    
    # Создаем колонки для отображения прав
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**✅ Разрешенные действия:**")
        if permissions["can_view"]:
            st.write("• 👁️ Просмотр данных")
        if permissions["can_edit"]:
            st.write("• ✏️ Редактирование данных")
        if permissions["can_create"]:
            st.write("• ➕ Создание новых записей")
        if permissions["can_manage_users"]:
            st.write("• 👥 Управление пользователями")
        if permissions["can_manage_content"]:
            st.write("• 📝 Управление контентом")
        if permissions["can_access_admin_panel"]:
            st.write("• 🏠 Доступ к админ-панели")
        if permissions["can_manage_roles"]:
            st.write("• 👑 Управление ролями")
    
    with col2:
        st.write("**❌ Запрещенные действия:**")
        if not permissions["can_delete"]:
            st.write("• 🗑️ Удаление данных")
        if not permissions["can_edit"]:
            st.write("• ✏️ Редактирование данных")
        if not permissions["can_create"]:
            st.write("• ➕ Создание новых записей")
        if not permissions["can_manage_users"]:
            st.write("• 👥 Управление пользователями")
        if not permissions["can_manage_content"]:
            st.write("• 📝 Управление контентом")
        if not permissions["can_access_admin_panel"]:
            st.write("• 🏠 Доступ к админ-панели")

def create_role_based_ui(user_role: str, section_name: str, 
                         view_component, edit_component=None, 
                         delete_component=None, create_component=None):
    """
    Создать UI на основе ролей пользователя
    
    Args:
        user_role: Роль пользователя
        section_name: Название раздела
        view_component: Компонент для просмотра
        edit_component: Компонент для редактирования (опционально)
        delete_component: Компонент для удаления (опционально)
        create_component: Компонент для создания (опционально)
    """
    permissions = get_user_permissions(user_role)
    
    st.subheader(f"📋 {section_name}")
    
    # Показываем компонент просмотра
    if permissions["can_view"]:
        view_component()
    else:
        show_access_denied(f"У вас нет прав для просмотра раздела '{section_name}'")
        return
    
    # Показываем компонент редактирования
    if edit_component and permissions["can_edit"]:
        st.write("---")
        st.write("**✏️ Редактирование:**")
        edit_component()
    
    # Показываем компонент создания
    if create_component and permissions["can_create"]:
        st.write("---")
        st.write("**➕ Создание:**")
        create_component()
    
    # Показываем компонент удаления
    if delete_component and permissions["can_delete"]:
        st.write("---")
        st.write("**🗑️ Удаление:**")
        delete_component()
    
    # Показываем информацию о правах
    if not any([permissions["can_edit"], permissions["can_create"], permissions["can_delete"]]):
        st.info("ℹ️ У вас есть права только на просмотр данных")
