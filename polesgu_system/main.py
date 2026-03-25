"""
main.py - Точка входа в систему оценки успеваемости ПолесГУ
Запускает серверную часть и клиентский интерфейс
"""

import sys
import threading
from server import initialize_server, get_db_api


def main():
    """Основная функция запуска"""
    print("=" * 60)
    print("🎓 Информационно-аналитическая система ПолесГУ")
    print("   Оценка успеваемости студентов инженерного факультета")
    print("=" * 60)
    print()
    
    # Инициализация сервера (БД + демо-данные)
    print("⏳ Инициализация базы данных...")
    try:
        initialize_server()
        print("✅ База данных готова!")
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        sys.exit(1)
    
    print()
    print("📊 Демо-данные:")
    print("   • Администратор: admin / RwQNt")
    print("   • Преподаватели: teacher1, teacher2, teacher3 / password")
    print("   • Студенты: student1...student250 / password")
    print()
    print("🚀 Запуск графического интерфейса...")
    print("-" * 60)
    
    # Импорт и запуск клиента
    try:
        from client import run_client
        run_client()
    except Exception as e:
        print(f"❌ Ошибка запуска клиента: {e}")
        print("\nУбедитесь, что все зависимости установлены:")
        print("   pip install -r requirements.txt")
        sys.exit(1)


if __name__ == "__main__":
    main()
