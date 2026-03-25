"""
server.py - Серверная часть системы оценки успеваемости ПолесГУ
Отвечает за:
- Подключение и управление БД SQLite
- Бизнес-логику (расчет рейтингов, фильтрация, валидация)
- Инициализацию БД и заполнение демо-данными
- API-методы для клиента
"""

import sqlite3
import bcrypt
import random
import threading
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Optional, List, Dict, Any, Tuple
import pandas as pd

# Константы
DB_NAME = "polesgu_system.db"
ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "RwQNt"

# Виды контроля
CONTROL_TYPES = ["Лекция", "Лабораторная", "Практическая", "Экзамен", "Зачет", "Курсовая"]

# Глобальный кэш для аналитики
analytics_cache = {}
cache_lock = threading.Lock()


def invalidate_cache():
    """Очистка кэша аналитики при изменении данных"""
    global analytics_cache
    with cache_lock:
        analytics_cache.clear()


def get_db_connection():
    """Создание подключения к БД"""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Инициализация базы данных и создание таблиц"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'student')),
            full_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Таблица студентов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            group_name TEXT NOT NULL,
            course INTEGER NOT NULL,
            specialty TEXT NOT NULL,
            faculty TEXT DEFAULT 'Инженерный факультет',
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    # Таблица дисциплин
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS disciplines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            department TEXT NOT NULL,
            teacher_id INTEGER,
            FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE SET NULL
        )
    """)
    
    # Таблица оценок
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            discipline_id INTEGER NOT NULL,
            value INTEGER,
            pass_fail BOOLEAN DEFAULT 0,
            pass_value BOOLEAN,
            control_type TEXT NOT NULL,
            date DATE NOT NULL,
            semester INTEGER NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (discipline_id) REFERENCES disciplines(id) ON DELETE CASCADE
        )
    """)
    
    # Таблица логов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """Хеширование пароля через bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Проверка пароля"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def seed_data():
    """Заполнение БД демо-данными при первом запуске"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Проверяем, есть ли уже данные
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    # Создаем администратора
    admin_hash = hash_password(ADMIN_PASSWORD)
    cursor.execute(
        "INSERT INTO users (login, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
        (ADMIN_LOGIN, admin_hash, 'admin', 'Администратор Системы')
    )
    admin_id = cursor.lastrowid
    
    # Создаем преподавателей
    teachers = [
        ("teacher1", "Иванов Иван Иванович", "Математика и физика"),
        ("teacher2", "Петров Петр Петрович", "Программирование"),
        ("teacher3", "Сидорова Анна Сергеевна", "Сопротивление материалов"),
    ]
    
    teacher_ids = []
    for login, full_name, dept in teachers:
        pwd_hash = hash_password("password")
        cursor.execute(
            "INSERT INTO users (login, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
            (login, pwd_hash, 'teacher', full_name)
        )
        teacher_ids.append(cursor.lastrowid)
    
    # Создаем дисциплины
    disciplines_list = [
        ("Высшая математика", "Кафедра математики", teacher_ids[0]),
        ("Физика", "Кафедра физики", teacher_ids[0]),
        ("Программирование", "Кафедра информатики", teacher_ids[1]),
        ("Базы данных", "Кафедра информатики", teacher_ids[1]),
        ("Сопротивление материалов", "Кафедра механики", teacher_ids[2]),
        ("Теоретическая механика", "Кафедра механики", teacher_ids[2]),
        ("Инженерная графика", "Кафедра графики", teacher_ids[1]),
        ("Электротехника", "Кафедра электроники", teacher_ids[0]),
        ("Материаловедение", "Кафедра технологии", teacher_ids[2]),
        ("Экономика", "Кафедра экономики", teacher_ids[0]),
        ("Иностранный язык", "Кафедра языков", teacher_ids[1]),
        ("Философия", "Кафедра гуманитарных наук", teacher_ids[2]),
    ]
    
    discipline_ids = []
    for name, dept, tid in disciplines_list:
        cursor.execute(
            "INSERT INTO disciplines (name, department, teacher_id) VALUES (?, ?, ?)",
            (name, dept, tid)
        )
        discipline_ids.append(cursor.lastrowid)
    
    # Генерируем студентов (250 человек, 10 групп)
    groups = [
        ("ИВТ-11", 1, "Информационные системы"),
        ("ИВТ-12", 1, "Информационные системы"),
        ("ИВТ-21", 2, "Информационные системы"),
        ("ИВТ-22", 2, "Информационные системы"),
        ("Мех-11", 1, "Машиностроение"),
        ("Мех-12", 1, "Машиностроение"),
        ("Мех-21", 2, "Машиностроение"),
        ("Мех-22", 2, "Машиностроение"),
        ("Энер-11", 1, "Энергетика"),
        ("Энер-21", 2, "Энергетика"),
    ]
    
    first_names = ["Александр", "Дмитрий", "Максим", "Сергей", "Андрей", "Алексей", "Артем", "Илья", "Кирилл", "Михаил",
                   "Анастасия", "Мария", "Елена", "Дарья", "Алина", "Ирина", "Екатерина", "Анна", "Ольга", "Наталья"]
    last_names = ["Иванов", "Смирнов", "Кузнецов", "Попов", "Васильев", "Петров", "Соколов", "Михайлов", "Новиков", "Федоров",
                  "Козлов", "Степанов", "Титов", "Павлов", "Семенов", "Григорьев", "Алексеев", "Владимиров", "Николаев", "Орлов"]
    
    student_count = 0
    for group_name, course, specialty in groups:
        students_in_group = 25  # 25 студентов в группе
        for i in range(students_in_group):
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            full_name = f"{last_name} {first_name}"
            login = f"student{student_count + 1}"
            pwd_hash = hash_password("password")
            
            cursor.execute(
                "INSERT INTO users (login, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
                (login, pwd_hash, 'student', full_name)
            )
            user_id = cursor.lastrowid
            
            cursor.execute(
                "INSERT INTO students (user_id, group_name, course, specialty, faculty) VALUES (?, ?, ?, ?, ?)",
                (user_id, group_name, course, specialty, 'Инженерный факультет')
            )
            
            # Генерируем оценки (~10 оценок на студента)
            student_id = cursor.lastrowid
            num_grades = random.randint(8, 12)
            
            for _ in range(num_grades):
                discipline_id = random.choice(discipline_ids)
                control_type = random.choice(CONTROL_TYPES)
                
                # Реалистичное распределение оценок: больше 7-9, меньше 2-4
                grade_rand = random.random()
                if grade_rand < 0.05:  # 5% двоек-троек
                    grade = random.randint(2, 4)
                elif grade_rand < 0.20:  # 15% четверок
                    grade = random.randint(5, 6)
                elif grade_rand < 0.60:  # 40% семерок-восьмерок
                    grade = random.randint(7, 8)
                else:  # 40% девяток-десяток
                    grade = random.randint(9, 10)
                
                # Для зачетов
                if control_type == "Зачет":
                    grade = None
                    pass_value = random.random() > 0.1  # 90% сдали
                
                date = datetime.now() - timedelta(days=random.randint(1, 180))
                semester = 1 if date.month <= 6 else 2
                
                cursor.execute(
                    """INSERT INTO grades (student_id, discipline_id, value, pass_fail, pass_value, 
                       control_type, date, semester) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (student_id, discipline_id, grade, 
                     1 if control_type == "Зачет" else 0,
                     pass_value if control_type == "Зачет" else None,
                     control_type, date.strftime('%Y-%m-%d'), semester)
                )
            
            student_count += 1
    
    # Добавляем лог о создании демо-данных
    cursor.execute(
        "INSERT INTO logs (user_id, action, details) VALUES (?, ?, ?)",
        (admin_id, 'SYSTEM_INIT', 'Созданы демо-данные: 250 студентов, 12 дисциплин, ~2500 оценок')
    )
    
    conn.commit()
    conn.close()
    print("База данных успешно инициализирована и заполнена демо-данными!")


class DatabaseAPI:
    """Класс для работы с базой данных (API для клиента)"""
    
    def __init__(self):
        self.conn = get_db_connection()
        self.conn.row_factory = sqlite3.Row
    
    def close(self):
        self.conn.close()
    
    # === Аутентификация ===
    
    def authenticate(self, login: str, password: str) -> Optional[Dict]:
        """Аутентификация пользователя"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE login = ?", (login,))
        user = cursor.fetchone()
        
        if user and verify_password(password, user['password_hash']):
            return {
                'id': user['id'],
                'login': user['login'],
                'role': user['role'],
                'full_name': user['full_name']
            }
        return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Получение пользователя по ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user:
            return dict(user)
        return None
    
    # === Логи ===
    
    def log_action(self, user_id: int, action: str, details: str = None):
        """Запись действия в лог"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO logs (user_id, action, details) VALUES (?, ?, ?)",
            (user_id, action, details)
        )
        self.conn.commit()
    
    def get_logs(self, user_id: int = None, limit: int = 100) -> List[Dict]:
        """Получение логов"""
        cursor = self.conn.cursor()
        if user_id:
            cursor.execute(
                """SELECT l.*, u.full_name, u.role 
                   FROM logs l JOIN users u ON l.user_id = u.id 
                   WHERE l.user_id = ? ORDER BY l.timestamp DESC LIMIT ?""",
                (user_id, limit)
            )
        else:
            cursor.execute(
                """SELECT l.*, u.full_name, u.role 
                   FROM logs l JOIN users u ON l.user_id = u.id 
                   ORDER BY l.timestamp DESC LIMIT ?""",
                (limit,)
            )
        return [dict(row) for row in cursor.fetchall()]
    
    # === Студенты ===
    
    def get_all_students(self, group_filter: str = None, course_filter: int = None, 
                         search_query: str = None) -> List[Dict]:
        """Получение списка студентов с фильтрацией"""
        cursor = self.conn.cursor()
        
        query = """
            SELECT s.*, u.full_name, u.login
            FROM students s
            JOIN users u ON s.user_id = u.id
            WHERE 1=1
        """
        params = []
        
        if group_filter:
            query += " AND s.group_name = ?"
            params.append(group_filter)
        
        if course_filter:
            query += " AND s.course = ?"
            params.append(course_filter)
        
        if search_query:
            query += " AND u.full_name LIKE ?"
            params.append(f"%{search_query}%")
        
        query += " ORDER BY s.group_name, u.full_name"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_student_by_id(self, student_id: int) -> Optional[Dict]:
        """Получение студента по ID"""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT s.*, u.full_name, u.login
               FROM students s
               JOIN users u ON s.user_id = u.id
               WHERE s.id = ?""",
            (student_id,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    
    def get_student_grades(self, student_id: int) -> List[Dict]:
        """Получение оценок студента"""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT g.*, d.name as discipline_name
               FROM grades g
               JOIN disciplines d ON g.discipline_id = d.id
               WHERE g.student_id = ?
               ORDER BY g.date DESC""",
            (student_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    # === Дисциплины ===
    
    def get_all_disciplines(self) -> List[Dict]:
        """Получение всех дисциплин"""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT d.*, u.full_name as teacher_name
               FROM disciplines d
               LEFT JOIN users u ON d.teacher_id = u.id
               ORDER BY d.name"""
        )
        return [dict(row) for row in cursor.fetchall()]
    
    # === Оценки ===
    
    def get_grades_for_group(self, group_name: str, discipline_id: int) -> List[Dict]:
        """Получение оценок для группы по предмету"""
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT s.id as student_id, u.full_name, g.value, g.pass_fail, g.pass_value, 
                      g.control_type, g.date, g.id as grade_id
               FROM students s
               JOIN users u ON s.user_id = u.id
               LEFT JOIN grades g ON s.id = g.student_id AND g.discipline_id = ?
               WHERE s.group_name = ?
               ORDER BY u.full_name""",
            (discipline_id, group_name)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def add_grade(self, student_id: int, discipline_id: int, value: int, 
                  control_type: str, date: str, semester: int, 
                  user_id: int, pass_value: bool = None) -> int:
        """Добавление оценки"""
        cursor = self.conn.cursor()
        
        is_pass_fail = 1 if control_type == "Зачет" else 0
        
        cursor.execute(
            """INSERT INTO grades (student_id, discipline_id, value, pass_fail, pass_value,
                       control_type, date, semester)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (student_id, discipline_id, value, is_pass_fail, pass_value, 
             control_type, date, semester)
        )
        
        grade_id = cursor.lastrowid
        
        # Логирование
        details = f"Добавлена оценка {value if value else ('Зачтено' if pass_value else 'Не зачтено')} ({control_type})"
        self.log_action(user_id, 'GRADE_ADD', details)
        
        self.conn.commit()
        invalidate_cache()
        return grade_id
    
    def update_grade(self, grade_id: int, new_value: int, user_id: int, 
                     pass_value: bool = None) -> bool:
        """Обновление оценки с логированием 'было/стало'"""
        cursor = self.conn.cursor()
        
        # Получаем старое значение
        cursor.execute("SELECT value, pass_value, control_type FROM grades WHERE id = ?", (grade_id,))
        old_row = cursor.fetchone()
        
        if not old_row:
            return False
        
        old_value = old_row['value']
        old_pass = old_row['pass_value']
        control_type = old_row['control_type']
        
        # Обновляем
        if control_type == "Зачет":
            cursor.execute(
                "UPDATE grades SET pass_value = ? WHERE id = ?",
                (pass_value, grade_id)
            )
            details = f"Изменен зачет: {'Зачтено' if old_pass else 'Не зачтено'} -> {'Зачтено' if pass_value else 'Не зачтено'}"
        else:
            cursor.execute(
                "UPDATE grades SET value = ? WHERE id = ?",
                (new_value, grade_id)
            )
            details = f"Изменена оценка: {old_value} -> {new_value}"
        
        # Логирование
        self.log_action(user_id, 'GRADE_UPDATE', details)
        
        self.conn.commit()
        invalidate_cache()
        return True
    
    # === Аналитика (с кэшированием) ===
    
    @lru_cache(maxsize=128)
    def _get_cached_analytics(self, cache_key: str) -> Dict:
        """Внутренний метод для кэширования аналитики"""
        # Этот метод вызывается с ключом, который включает параметры запроса
        return self._calculate_analytics()
    
    def _calculate_analytics(self) -> Dict:
        """Расчет всей аналитики"""
        cursor = self.conn.cursor()
        
        # Общий средний балл
        cursor.execute("SELECT AVG(value) as avg_grade FROM grades WHERE value IS NOT NULL")
        avg_grade = cursor.fetchone()['avg_grade'] or 0
        
        # Успеваемость (% оценок > 3)
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN value > 3 THEN 1 END) * 100.0 / COUNT(*) as success_rate
            FROM grades WHERE value IS NOT NULL
        """)
        success_rate = cursor.fetchone()['success_rate'] or 0
        
        # Качество знаний (% оценок 8-10)
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN value >= 8 THEN 1 END) * 100.0 / COUNT(*) as quality_rate
            FROM grades WHERE value IS NOT NULL
        """)
        quality_rate = cursor.fetchone()['quality_rate'] or 0
        
        # Количество студентов
        cursor.execute("SELECT COUNT(*) FROM students")
        total_students = cursor.fetchone()[0]
        
        # Распределение оценок
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN value >= 9 THEN 1 ELSE 0 END) as excellent,
                SUM(CASE WHEN value >= 7 AND value < 9 THEN 1 ELSE 0 END) as good,
                SUM(CASE WHEN value >= 4 AND value < 7 THEN 1 ELSE 0 END) as satisfactory,
                SUM(CASE WHEN value <= 3 THEN 1 ELSE 0 END) as poor
            FROM grades WHERE value IS NOT NULL
        """)
        dist_row = cursor.fetchone()
        grade_distribution = {
            'excellent': dist_row['excellent'] or 0,
            'good': dist_row['good'] or 0,
            'satisfactory': dist_row['satisfactory'] or 0,
            'poor': dist_row['poor'] or 0
        }
        
        return {
            'avg_grade': round(avg_grade, 2),
            'success_rate': round(success_rate, 2),
            'quality_rate': round(quality_rate, 2),
            'total_students': total_students,
            'grade_distribution': grade_distribution
        }
    
    def get_analytics(self) -> Dict:
        """Получение аналитики с кэшированием"""
        cache_key = "main_analytics"
        
        with cache_lock:
            if cache_key in analytics_cache:
                return analytics_cache[cache_key]
        
        result = self._calculate_analytics()
        
        with cache_lock:
            analytics_cache[cache_key] = result
        
        return result
    
    def get_at_risk_students(self, threshold: int = 4) -> List[Dict]:
        """Студенты в группе риска (оценки <= threshold)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT s.id, u.full_name, s.group_name, s.course,
                   MIN(g.value) as min_grade,
                   AVG(g.value) as avg_grade
            FROM students s
            JOIN users u ON s.user_id = u.id
            JOIN grades g ON s.id = g.student_id
            WHERE g.value <= ?
            GROUP BY s.id
            ORDER BY avg_grade ASC
            LIMIT 20
        """, (threshold,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_predicted_risk_students(self) -> List[Dict]:
        """Прогнозирование риска отсева на основе тренда"""
        cursor = self.conn.cursor()
        
        # Получаем всех студентов с их оценками по времени
        cursor.execute("""
            SELECT s.id, u.full_name, s.group_name,
                   g.value, g.date
            FROM students s
            JOIN users u ON s.user_id = u.id
            JOIN grades g ON s.id = g.student_id
            WHERE g.value IS NOT NULL
            ORDER BY s.id, g.date
        """)
        
        rows = cursor.fetchall()
        
        # Группируем по студентам
        student_grades = {}
        for row in rows:
            sid = row['id']
            if sid not in student_grades:
                student_grades[sid] = {
                    'full_name': row['full_name'],
                    'group_name': row['group_name'],
                    'grades': [],
                    'dates': []
                }
            student_grades[sid]['grades'].append(row['value'])
            student_grades[sid]['dates'].append(row['date'])
        
        risk_students = []
        
        for sid, data in student_grades.items():
            grades = data['grades']
            if len(grades) < 3:
                continue
            
            # Разделяем на первые и последние оценки
            mid = len(grades) // 2
            first_half_avg = sum(grades[:mid]) / len(grades[:mid])
            second_half_avg = sum(grades[mid:]) / len(grades[mid:])
            
            # Вычисляем тренд
            trend = ((second_half_avg - first_half_avg) / first_half_avg) * 100 if first_half_avg > 0 else 0
            
            current_avg = sum(grades) / len(grades)
            
            # Если тренд отрицательный и значительный
            if trend < -10 and current_avg < 7:
                risk_prob = min(95, abs(trend) * 3)
                risk_students.append({
                    'id': sid,
                    'full_name': data['full_name'],
                    'group_name': data['group_name'],
                    'current_avg': round(current_avg, 2),
                    'trend': round(trend, 2),
                    'risk_probability': round(risk_prob, 1)
                })
        
        # Сортируем по вероятности риска
        risk_students.sort(key=lambda x: x['risk_probability'], reverse=True)
        return risk_students[:20]
    
    def get_heatmap_data(self) -> Dict:
        """Данные для тепловой карты проблемных дисциплин"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT d.name as discipline, 
                   COUNT(CASE WHEN g.value <= 4 THEN 1 END) * 100.0 / COUNT(*) as poor_rate,
                   COUNT(*) as total_grades
            FROM disciplines d
            JOIN grades g ON d.id = g.discipline_id
            WHERE g.value IS NOT NULL
            GROUP BY d.id
            ORDER BY poor_rate DESC
        """)
        
        return {row['discipline']: round(row['poor_rate'], 2) for row in cursor.fetchall()}
    
    def get_group_comparison(self, group1: str, group2: str) -> Dict:
        """Сравнение двух групп"""
        cursor = self.conn.cursor()
        
        result = {}
        for group in [group1, group2]:
            cursor.execute("""
                SELECT AVG(g.value) as avg_grade,
                       COUNT(CASE WHEN g.value > 3 THEN 1 END) * 100.0 / COUNT(*) as success_rate,
                       COUNT(CASE WHEN g.value >= 8 THEN 1 END) * 100.0 / COUNT(*) as quality_rate
                FROM students s
                JOIN grades g ON s.id = g.student_id
                WHERE s.group_name = ? AND g.value IS NOT NULL
            """, (group,))
            
            row = cursor.fetchone()
            result[group] = {
                'avg_grade': round(row['avg_grade'] or 0, 2),
                'success_rate': round(row['success_rate'] or 0, 2),
                'quality_rate': round(row['quality_rate'] or 0, 2)
            }
        
        return result
    
    def get_top_students(self, limit: int = 10) -> List[Dict]:
        """Топ студентов по среднему баллу"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.id, u.full_name, s.group_name,
                   AVG(g.value) as avg_grade,
                   COUNT(g.id) as grades_count
            FROM students s
            JOIN users u ON s.user_id = u.id
            JOIN grades g ON s.id = g.student_id
            WHERE g.value IS NOT NULL
            GROUP BY s.id
            HAVING COUNT(g.id) >= 3
            ORDER BY avg_grade DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]
    
    def get_group_ranking(self) -> List[Dict]:
        """Рейтинг групп по среднему баллу"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.group_name,
                   AVG(g.value) as avg_grade,
                   COUNT(DISTINCT s.id) as student_count
            FROM students s
            JOIN grades g ON s.id = g.student_id
            WHERE g.value IS NOT NULL
            GROUP BY s.group_name
            ORDER BY avg_grade DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    # === Пользователи (только админ) ===
    
    def get_all_users(self) -> List[Dict]:
        """Получение всех пользователей (сортировка: admin, teacher, student)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM users
            ORDER BY 
                CASE role
                    WHEN 'admin' THEN 1
                    WHEN 'teacher' THEN 2
                    WHEN 'student' THEN 3
                END,
                full_name
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    def promote_to_teacher(self, user_id: int, admin_id: int) -> bool:
        """Повышение роли до преподавателя"""
        cursor = self.conn.cursor()
        
        # Проверяем текущую роль
        cursor.execute("SELECT role, full_name FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user or user['role'] != 'student':
            return False
        
        cursor.execute("UPDATE users SET role = 'teacher' WHERE id = ?", (user_id,))
        
        # Логирование
        self.log_action(admin_id, 'ROLE_CHANGE', f"Пользователь {user['full_name']} повышен до преподавателя")
        
        self.conn.commit()
        return True
    
    def reset_user_password(self, user_id: int, admin_id: int, new_password: str = "password") -> bool:
        """Сброс пароля пользователя"""
        cursor = self.conn.cursor()
        
        new_hash = hash_password(new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
        
        cursor.execute("SELECT full_name FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        self.log_action(admin_id, 'PASSWORD_RESET', f"Сброшен пароль пользователю {user['full_name']}")
        
        self.conn.commit()
        return True
    
    # === Настройки ===
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """Смена пароля пользователя"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user or not verify_password(old_password, user['password_hash']):
            return False
        
        new_hash = hash_password(new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
        self.conn.commit()
        
        self.log_action(user_id, 'PASSWORD_CHANGE', 'Пароль изменен')
        return True
    
    def update_full_name(self, user_id: int, new_name: str) -> bool:
        """Обновление ФИО"""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET full_name = ? WHERE id = ?", (new_name, user_id))
        self.conn.commit()
        self.log_action(user_id, 'PROFILE_UPDATE', f"ФИО изменено на {new_name}")
        return True
    
    def get_available_groups(self) -> List[str]:
        """Получение списка всех групп"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT group_name FROM students ORDER BY group_name")
        return [row['group_name'] for row in cursor.fetchall()]


# Singleton экземпляр API
db_api = None


def get_db_api() -> DatabaseAPI:
    """Получение экземпляра DatabaseAPI"""
    global db_api
    if db_api is None:
        db_api = DatabaseAPI()
    return db_api


def initialize_server():
    """Инициализация сервера (БД + демо-данные)"""
    init_database()
    seed_data()
    print("Сервер готов к работе!")


if __name__ == "__main__":
    initialize_server()
