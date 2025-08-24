#!/usr/bin/env python3
"""
Скрипт для удаления пользователя admin из таблицы admin_users
"""

from database.database import AdminDatabase

def main():
    print("🗑️ Удаляем пользователя admin из admin_users...")
    
    try:
        db = AdminDatabase()
        
        # Проверяем текущих пользователей
        print("\n📋 Текущие пользователи в admin_users:")
        users = db.get_all_admin_users()
        for user in users:
            print(f"  - {user[1]} (ID: {user[0]}, Active: {user[4]})")
        
        # Удаляем пользователя admin
        print(f"\n🔍 Ищем пользователя 'admin'...")
        admin_user = db.get_admin_user_by_username('admin')
        
        if admin_user:
            print(f"✅ Найден пользователь: {admin_user[1]} (ID: {admin_user[0]})")
            
            # Удаляем пользователя
            success = db.delete_admin_user('admin')
            if success:
                print("✅ Пользователь admin успешно удален (деактивирован)")
            else:
                print("❌ Ошибка при удалении пользователя admin")
        else:
            print("ℹ️ Пользователь admin не найден в admin_users")
        
        # Проверяем результат
        print("\n📋 Пользователи после удаления:")
        users_after = db.get_all_admin_users()
        for user in users_after:
            print(f"  - {user[1]} (ID: {user[0]}, Active: {user[4]})")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
