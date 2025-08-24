"""
Модуль безопасности для админ-панели
Включает аутентификацию, авторизацию и защиту от атак
"""

from .auth import authenticate_user, get_user_role, get_user_info, auth, get_auth
from .security import security_manager, SecurityManager
from .access_control import (
    get_user_permissions,
    check_permission,
    require_permission,
    show_access_denied,
    can_access_page,
    get_accessible_pages,
    show_user_permissions_info,
    create_role_based_ui,
)

__all__ = [
    "authenticate_user",
    "get_user_role",
    "get_user_info",
    "auth",
    "get_auth",
    "security_manager",
    "SecurityManager",
    "get_user_permissions",
    "check_permission",
    "require_permission",
    "show_access_denied",
    "can_access_page",
    "get_accessible_pages",
    "show_user_permissions_info",
    "create_role_based_ui",
]
