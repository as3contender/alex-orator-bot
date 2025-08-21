#!/usr/bin/env python3

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict, Any
from urllib.parse import quote_plus
import os
from datetime import datetime


class AdminDatabase:
    def __init__(self):
        self.conn = None
        # Подключение к существующей базе данных
        password = "?%Lv6u*TgAD#+rMRcHob"
        encoded_password = quote_plus(password)
        self.database_url = f"postgresql://alex_orator:{encoded_password}@localhost:5434/app_db"
        print(f"🔗 Подключение к базе: postgresql://alex_orator:***@localhost:5434/app_db")
    
    def connect(self):
        """Подключение к базе данных"""
        try:
            self.conn = psycopg2.connect(self.database_url)
            print("✅ Подключение к базе данных установлено")
        except Exception as e:
            print(f"❌ Ошибка подключения к базе данных: {e}")
            raise
    
    def disconnect(self):
        """Отключение от базы данных"""
        if self.conn:
            self.conn.close()
            self.conn = None
            print("✅ Отключение от базы данных выполнено")
    
    def get_all_bot_content(self, language: str = None, is_active: bool = None) -> List[Dict[str, Any]]:
        """Получить весь контент бота"""
        try:
            if not self.conn:
                self.connect()
            
            query = "SELECT id, content_key, content_text, language, is_active, created_at, updated_at FROM bot_content WHERE 1=1"
            params = []
            param_count = 0
            
            if language:
                param_count += 1
                query += f" AND language = %s"
                params.append(language)
            
            if is_active is not None:
                param_count += 1
                query += f" AND is_active = %s"
                params.append(is_active)
            
            query += " ORDER BY content_key, language"
            
            print(f"🔍 Выполняем запрос: {query}")
            print(f"📝 Параметры: {params}")
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]
                print(f"✅ Получено {len(result)} записей")
                return result
        except Exception as e:
            print(f"❌ Ошибка получения контента: {e}")
            return []
    
    def create_bot_content(self, content_key: str, content_text: str, language: str = "ru", is_active: bool = True) -> Optional[Dict[str, Any]]:
        """Создать новый контент"""
        try:
            if not self.conn:
                self.connect()
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO bot_content (content_key, content_text, language, is_active)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, content_key, content_text, language, is_active, created_at, updated_at
                    """,
                    (content_key, content_text, language, is_active)
                )
                row = cursor.fetchone()
                self.conn.commit()
                return dict(row) if row else None
        except Exception as e:
            print(f"❌ Ошибка создания контента: {e}")
            if self.conn:
                self.conn.rollback()
            return None
    
    def update_bot_content(self, content_key: str, content_text: str, language: str = "ru") -> bool:
        """Обновить существующий контент"""
        try:
            if not self.conn:
                self.connect()
            
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE bot_content 
                    SET content_text = %s, updated_at = CURRENT_TIMESTAMP 
                    WHERE content_key = %s AND language = %s
                    """,
                    (content_text, content_key, language)
                )
                self.conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Ошибка обновления контента: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def delete_bot_content(self, content_key: str, language: str = "ru") -> bool:
        """Удалить контент (деактивировать)"""
        try:
            if not self.conn:
                self.connect()
            
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE bot_content SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP WHERE content_key = %s AND language = %s",
                    (content_key, language)
                )
                self.conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Ошибка удаления контента: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def permanently_delete_bot_content(self, content_key: str, language: str = "ru") -> bool:
        """Полностью удалить контент из базы данных"""
        try:
            if not self.conn:
                self.connect()
            
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM bot_content WHERE content_key = %s AND language = %s",
                    (content_key, language)
                )
                self.conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Ошибка полного удаления контента: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def get_users_with_problems(self) -> List[Dict[str, Any]]:
        """Получить пользователей с проблемными данными"""
        try:
            if not self.conn:
                self.connect()
            
            query = """
                SELECT id, telegram_id, username, first_name, last_name, 
                       gender, registration_date, total_sessions, 
                       feedback_count, is_active, created_at, updated_at
                FROM users 
                WHERE username IS NULL OR username = '' 
                   OR first_name IS NULL OR first_name = ''
                   OR last_name IS NULL OR last_name = ''
                   OR gender IS NULL OR gender = ''
                ORDER BY created_at DESC
            """
            
            print(f"🔍 Выполняем запрос: {query}")
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]
                print(f"✅ Получено {len(result)} пользователей с проблемными данными")
                return result
        except Exception as e:
            print(f"❌ Ошибка получения пользователей с проблемными данными: {e}")
            return []
    
    def fix_user_data(self, telegram_id: int, username: str = None, first_name: str = None, last_name: str = None, gender: str = None) -> bool:
        """Исправить данные пользователя"""
        try:
            if not self.conn:
                self.connect()
            
            # Формируем динамический UPDATE запрос
            update_fields = []
            params = []
            
            if username is not None:
                update_fields.append("username = %s")
                params.append(username)
            if first_name is not None:
                update_fields.append("first_name = %s")
                params.append(first_name)
            if last_name is not None:
                update_fields.append("last_name = %s")
                params.append(last_name)
            if gender is not None:
                update_fields.append("gender = %s")
                params.append(gender)
            
            if not update_fields:
                print("❌ Не указаны поля для обновления")
                return False
            
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            params.append(telegram_id)
            
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE telegram_id = %s"
            
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                self.conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Ошибка исправления данных пользователя: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def delete_problem_user(self, telegram_id: int) -> bool:
        """Удалить проблемного пользователя"""
        try:
            if not self.conn:
                self.connect()
            
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM users WHERE telegram_id = %s",
                    (telegram_id,)
                )
                self.conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Ошибка удаления пользователя: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def activate_bot_content(self, content_key: str, language: str = "ru") -> bool:
        """Активировать контент"""
        try:
            if not self.conn:
                self.connect()
            
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE bot_content SET is_active = TRUE, updated_at = CURRENT_TIMESTAMP WHERE content_key = %s AND language = %s",
                    (content_key, language)
                )
                self.conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Ошибка активации контента: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def execute_sql_file(self, sql_file_path: str) -> List[Dict[str, Any]]:
        """Выполнить SQL из файла и вернуть результат"""
        try:
            # Разрешаем относительный путь от корня проекта
            if not os.path.isabs(sql_file_path):
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
                sql_file_path = os.path.abspath(os.path.join(base_dir, sql_file_path))
            
            print(f"📁 Выполняем SQL из файла: {sql_file_path}")
            
            with open(sql_file_path, "r", encoding="utf-8") as f:
                sql = f.read()
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(sql)
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]
                print(f"✅ SQL выполнен, получено {len(result)} строк")
                return result
        except Exception as e:
            print(f"❌ Ошибка выполнения SQL из файла '{sql_file_path}': {e}")
            return []

    def get_language_statistics(self):
        """Получает статистику по языкам"""
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT language, COUNT(*) as count 
                FROM bot_content 
                WHERE language IS NOT NULL 
                GROUP BY language 
                ORDER BY count DESC
            """)
            return cursor.fetchall()
        except Exception as e:
            print(f"Ошибка получения статистики по языкам: {e}")
            return []

    def get_table_columns(self):
        """Получает информацию о колонках таблицы bot_content"""
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = 'bot_content' 
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            
            # Добавляем дополнительные поля для интерфейса
            enhanced_columns = []
            for col in columns:
                enhanced_col = dict(col)
                # Добавляем поля для интерфейса редактирования
                enhanced_col['tags'] = self._get_column_tags(col['column_name'])
                enhanced_col['placeholder'] = self._get_column_placeholder(col['column_name'])
                enhanced_col['description'] = self._get_column_description(col['column_name'])
                enhanced_columns.append(enhanced_col)
            
            return enhanced_columns
        except Exception as e:
            print(f"Ошибка получения информации о колонках: {e}")
            return []

    def _get_column_tags(self, column_name):
        """Получает теги для колонки (заглушка)"""
        tags_map = {
            'key': 'ключ, основной, автоматический',
            'content': 'контент, текст, основной',
            'language': 'язык, локализация',
            'status': 'статус, состояние',
            'created_at': 'дата, время, создание',
            'updated_at': 'дата, время, обновление'
        }
        return tags_map.get(column_name, 'общий')

    def _get_column_placeholder(self, column_name):
        """Получает placeholder для колонки (заглушка)"""
        placeholder_map = {
            'key': '2025-03-02_00T3-012208',
            'content': 'Введите текст контента...',
            'language': 'ru, en, de',
            'status': 'active, inactive, draft',
            'created_at': '2025-01-01 00:00:00',
            'updated_at': '2025-01-01 00:00:00'
        }
        return placeholder_map.get(column_name, 'Введите значение...')

    def _get_column_description(self, column_name):
        """Получает описание для колонки (заглушка)"""
        description_map = {
            'key': 'Основной ключ таблицы (автоматически создан)',
            'content': 'Основной контент сообщения бота',
            'language': 'Язык контента (ru, en, de)',
            'status': 'Статус контента (active, inactive, draft)',
            'created_at': 'Дата и время создания записи',
            'updated_at': 'Дата и время последнего обновления'
        }
        return description_map.get(column_name, 'Описание колонки')

    # ============================================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С АДМИНИСТРАТОРАМИ
    # ============================================================================
    
    def get_admin_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Получить администратора по username"""
        try:
            if not self.conn:
                self.connect()
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, username, hashed_password, full_name, role, is_active, 
                           last_login, created_at, updated_at
                    FROM admin_users 
                    WHERE username = %s AND is_active = TRUE
                """, (username,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"❌ Ошибка получения администратора: {e}")
            return None
    
    def update_admin_last_login(self, username: str) -> bool:
        """Обновить время последнего входа администратора"""
        try:
            if not self.conn:
                self.connect()
            
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE admin_users 
                    SET last_login = CURRENT_TIMESTAMP 
                    WHERE username = %s
                """, (username,))
                self.conn.commit()
                return True
        except Exception as e:
            print(f"❌ Ошибка обновления времени входа: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def create_admin_user(self, username: str, hashed_password: str, full_name: str, role: str = 'admin') -> Optional[Dict[str, Any]]:
        """Создать нового администратора"""
        try:
            if not self.conn:
                self.connect()
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    INSERT INTO admin_users (username, hashed_password, full_name, role)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, username, full_name, role, is_active, created_at, updated_at
                """, (username, hashed_password, full_name, role))
                row = cursor.fetchone()
                self.conn.commit()
                return dict(row) if row else None
        except Exception as e:
            print(f"❌ Ошибка создания администратора: {e}")
            if self.conn:
                self.conn.rollback()
            return None
    
    def update_admin_user(self, username: str, **kwargs) -> bool:
        """Обновить данные администратора"""
        try:
            if not self.conn:
                self.connect()
            
            # Формируем SET часть запроса динамически
            set_parts = []
            params = []
            for key, value in kwargs.items():
                if key in ['full_name', 'role', 'is_active', 'hashed_password']:
                    set_parts.append(f"{key} = %s")
                    params.append(value)
            
            if not set_parts:
                return False
            
            params.append(username)
            query = f"""
                UPDATE admin_users 
                SET {', '.join(set_parts)}
                WHERE username = %s
            """
            
            with self.conn.cursor() as cursor:
                cursor.execute(query, params)
                self.conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Ошибка обновления администратора: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def delete_admin_user(self, username: str) -> bool:
        """Удалить администратора (мягкое удаление - деактивация)"""
        try:
            if not self.conn:
                self.connect()
            
            with self.conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE admin_users 
                    SET is_active = FALSE 
                    WHERE username = %s
                """, (username,))
                self.conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"❌ Ошибка удаления администратора: {e}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def get_all_admin_users(self) -> List[Dict[str, Any]]:
        """Получить всех администраторов"""
        try:
            if not self.conn:
                self.connect()
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT id, username, full_name, role, is_active, 
                           last_login, created_at, updated_at
                    FROM admin_users 
                    ORDER BY created_at DESC
                """)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"❌ Ошибка получения списка администраторов: {e}")
            return []

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получить всех пользователей из таблицы users"""
        try:
            if not self.conn:
                self.connect()
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Сначала пробуем получить с ролью
                try:
                    cursor.execute("""
                        SELECT id, telegram_id, username, first_name, last_name, 
                               gender, registration_date, total_sessions, 
                               feedback_count, is_active, created_at, updated_at, password, role
                        FROM users 
                        ORDER BY created_at DESC
                    """)
                    rows = cursor.fetchall()
                    result = [dict(row) for row in rows]
                    print(f"✅ Получено {len(result)} пользователей с ролями")
                    return result
                except Exception as role_error:
                    print(f"⚠️ Ошибка при получении с ролями: {role_error}")
                    print("🔄 Пробуем получить без ролей...")
                    
                    # Fallback - получаем без роли
                    cursor.execute("""
                        SELECT id, telegram_id, username, first_name, last_name, 
                               gender, registration_date, total_sessions, 
                               feedback_count, is_active, created_at, updated_at, password
                        FROM users 
                        ORDER BY created_at DESC
                    """)
                    rows = cursor.fetchall()
                    result = [dict(row) for row in rows]
                    
                    # Добавляем роль по умолчанию для каждого пользователя
                    for user in result:
                        user['role'] = 'user'
                    
                    print(f"✅ Получено {len(result)} пользователей без ролей (установлена роль 'user' по умолчанию)")
                    return result
        except Exception as e:
            print(f"❌ Ошибка получения пользователей: {e}")
            return []

    def create_user(self, username: str, password: str, role: str = "user", 
                   full_name: str = None, email: str = None, 
                   telegram_id: str = None) -> bool:
        """Создать нового пользователя"""
        try:
            print(f"🔍 [DB] Начинаем создание пользователя: {username}")
            print(f"🎭 [DB] Роль пользователя: {role}")
            
            if not self.conn:
                print("🔗 [DB] Подключаемся к базе данных...")
                self.connect()
            
            # Генерируем UUID для пользователя
            import uuid
            user_id = str(uuid.uuid4())
            print(f"🆔 [DB] Сгенерирован ID: {user_id}")
            
            # Хешируем пароль (используем простой хеш для демонстрации)
            import hashlib
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            print(f"🔒 [DB] Пароль захеширован")
            
            # Подготавливаем данные
            first_name = full_name if full_name else username
            last_name = full_name if full_name else username
            telegram_id_val = telegram_id if telegram_id else None
            
            print(f"📝 [DB] Подготовленные данные:")
            print(f"   [DB] First name: {first_name}")
            print(f"   [DB] Last name: {last_name}")
            print(f"   [DB] Telegram ID: {telegram_id_val}")
            print(f"   [DB] Role: {role}")
            
            with self.conn.cursor() as cursor:
                print("📋 [DB] Выполняем INSERT запрос...")
                
                # Сначала проверяем, есть ли колонка role в таблице
                try:
                    cursor.execute("""
                        INSERT INTO users (id, username, first_name, last_name, 
                                         telegram_id, is_active, gender, password, role,
                                         created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        user_id, username, first_name, last_name, 
                        telegram_id_val, True, 'other', hashed_password, role,
                        datetime.now(), datetime.now()
                    ))
                    print(f"✅ [DB] INSERT с ролью выполнен, affected rows: {cursor.rowcount}")
                except Exception as role_error:
                    print(f"⚠️ [DB] Ошибка при вставке с ролью: {role_error}")
                    print("🔄 [DB] Пробуем вставить без роли...")
                    
                    # Fallback - вставляем без роли
                    cursor.execute("""
                        INSERT INTO users (id, username, first_name, last_name, 
                                         telegram_id, is_active, gender, password,
                                         created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        user_id, username, first_name, last_name, 
                        telegram_id_val, True, 'other', hashed_password,
                        datetime.now(), datetime.now()
                    ))
                    print(f"✅ [DB] INSERT без роли выполнен, affected rows: {cursor.rowcount}")
                
                self.conn.commit()
                print(f"✅ [DB] Пользователь {username} успешно создан")
                return True
        except Exception as e:
            print(f"❌ [DB] Ошибка создания пользователя: {e}")
            import traceback
            traceback.print_exc()
            if self.conn:
                self.conn.rollback()
            return False

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Получить пользователя по username из таблицы users"""
        try:
            if not self.conn:
                self.connect()
            
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Сначала пробуем получить с ролью
                try:
                    cursor.execute("""
                        SELECT id, username, first_name, last_name, 
                               telegram_id, is_active, gender, password, role,
                               created_at, updated_at
                        FROM users 
                        WHERE username = %s AND is_active = TRUE
                    """, (username,))
                    row = cursor.fetchone()
                    if row:
                        user_data = dict(row)
                        print(f"✅ Получен пользователь {username} с ролью: {user_data.get('role', 'user')}")
                        return user_data
                    return None
                except Exception as role_error:
                    print(f"⚠️ Ошибка при получении с ролью: {role_error}")
                    print("🔄 Пробуем получить без роли...")
                    
                    # Fallback - получаем без роли
                    cursor.execute("""
                        SELECT id, username, first_name, last_name, 
                               telegram_id, is_active, gender, password,
                               created_at, updated_at
                        FROM users 
                        WHERE username = %s AND is_active = TRUE
                    """, (username,))
                    row = cursor.fetchone()
                    if row:
                        user_data = dict(row)
                        user_data['role'] = 'user'  # Устанавливаем роль по умолчанию
                        print(f"✅ Получен пользователь {username} без роли (установлена роль 'user' по умолчанию)")
                        return user_data
                    return None
        except Exception as e:
            print(f"❌ Ошибка получения пользователя: {e}")
            return None

    def update_user_role(self, username: str, new_role: str) -> bool:
        """Обновить роль пользователя"""
        try:
            print(f"🔄 [DB] Обновляем роль пользователя {username} на {new_role}")
            
            if not self.conn:
                self.connect()
            
            with self.conn.cursor() as cursor:
                # Проверяем, есть ли колонка role в таблице
                try:
                    cursor.execute("""
                        UPDATE users 
                        SET role = %s, updated_at = %s
                        WHERE username = %s AND is_active = TRUE
                    """, (new_role, datetime.now(), username))
                    
                    if cursor.rowcount > 0:
                        self.conn.commit()
                        print(f"✅ [DB] Роль пользователя {username} успешно обновлена на {new_role}")
                        return True
                    else:
                        print(f"❌ [DB] Пользователь {username} не найден или неактивен")
                        return False
                        
                except Exception as role_error:
                    print(f"⚠️ [DB] Ошибка при обновлении роли: {role_error}")
                    print("🔄 [DB] Возможно, колонка role не существует")
                    return False
                    
        except Exception as e:
            print(f"❌ [DB] Ошибка обновления роли: {e}")
            if self.conn:
                self.conn.rollback()
            return False

    def delete_user(self, user_id: str) -> bool:
        """Удалить пользователя по ID"""
        try:
            print(f"🗑️ [DB] Удаляем пользователя с ID: {user_id}")
            
            if not self.conn:
                self.connect()
            
            with self.conn.cursor() as cursor:
                # Сначала получаем информацию о пользователе для логирования
                cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
                user_info = cursor.fetchone()
                username = user_info[0] if user_info else "Unknown"
                
                print(f"🗑️ [DB] Удаляем пользователя: {username}")
                
                # Удаляем пользователя
                cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
                
                if cursor.rowcount > 0:
                    self.conn.commit()
                    print(f"✅ [DB] Пользователь {username} успешно удален")
                    return True
                else:
                    print(f"❌ [DB] Пользователь с ID {user_id} не найден")
                    return False
                    
        except Exception as e:
            print(f"❌ [DB] Ошибка удаления пользователя: {e}")
            if self.conn:
                self.conn.rollback()
            return False


# Создание глобального экземпляра
db = AdminDatabase()


def init_database():
    """Инициализация подключения к базе данных"""
    db.connect()


def close_database():
    """Закрытие подключения к базе данных"""
    db.disconnect()


# Для использования в Streamlit
def get_db():
    """Получить экземпляр базы данных"""
    return db
