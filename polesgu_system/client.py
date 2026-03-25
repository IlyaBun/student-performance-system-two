"""
client.py - Клиентская часть системы оценки успеваемости ПолесГУ
Графический интерфейс на customtkinter
"""

import customtkinter as ctk
from tkinter import messagebox, ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
from typing import Optional, Dict, List
from datetime import datetime

# Импорт серверной части
from server import (
    initialize_server, get_db_api, DatabaseAPI, 
    CONTROL_TYPES, DB_NAME
)

# Настройки внешнего вида
ctk.set_appearance_mode("dark")  # Темная тема по умолчанию
ctk.set_default_color_theme("blue")

# Локализация
TRANSLATIONS = {
    'ru': {
        'title': 'ПолесГУ - Система оценки успеваемости',
        'login': 'Вход в систему',
        'username': 'Логин',
        'password': 'Пароль',
        'login_btn': 'Войти',
        'logout': 'Выход',
        'dashboard': 'Главная',
        'students': 'Студенты',
        'disciplines': 'Дисциплины',
        'grades': 'Оценки',
        'analytics': 'Аналитика',
        'users': 'Пользователи',
        'settings': 'Настройки',
        'profile': 'Профиль',
        'role_admin': 'Администратор',
        'role_teacher': 'Преподаватель',
        'role_student': 'Студент',
        'avg_grade': 'Средний балл',
        'success_rate': 'Успеваемость %',
        'quality_rate': 'Качество знаний %',
        'total_students': 'Всего студентов',
        'at_risk': 'Группа риска',
        'predicted_risk': 'Прогноз отсева',
        'heatmap': 'Проблемные предметы',
        'search': 'Поиск...',
        'filter_group': 'Группа',
        'filter_course': 'Курс',
        'add': 'Добавить',
        'edit': 'Редактировать',
        'delete': 'Удалить',
        'save': 'Сохранить',
        'cancel': 'Отмена',
        'group': 'Группа',
        'course': 'Курс',
        'specialty': 'Специальность',
        'full_name': 'ФИО',
        'discipline': 'Предмет',
        'control_type': 'Вид контроля',
        'grade_value': 'Оценка',
        'pass_fail': 'Зачет',
        'passed': 'Зачтено',
        'not_passed': 'Не зачтено',
        'date': 'Дата',
        'semester': 'Семестр',
        'action': 'Действие',
        'logs': 'Логи',
        'theme': 'Тема',
        'language': 'Язык',
        'change_password': 'Сменить пароль',
        'old_password': 'Старый пароль',
        'new_password': 'Новый пароль',
        'confirm_password': 'Подтвердите пароль',
        'promote_to_teacher': 'Назначить преподавателем',
        'reset_password': 'Сбросить пароль',
        'error': 'Ошибка',
        'success': 'Успешно',
        'confirm_delete': 'Вы уверены?',
        'no_data': 'Нет данных',
        'trend': 'Тренд',
        'risk_probability': 'Вероятность риска %',
        'comparison': 'Сравнение групп',
        'select_group': 'Выберите группу',
        'compare': 'Сравнить',
        'top_students': 'Лучшие студенты',
        'group_ranking': 'Рейтинг групп',
    },
    'en': {
        'title': 'PolesGU - Academic Performance System',
        'login': 'Login',
        'username': 'Username',
        'password': 'Password',
        'login_btn': 'Sign In',
        'logout': 'Logout',
        'dashboard': 'Dashboard',
        'students': 'Students',
        'disciplines': 'Disciplines',
        'grades': 'Grades',
        'analytics': 'Analytics',
        'users': 'Users',
        'settings': 'Settings',
        'profile': 'Profile',
        'role_admin': 'Administrator',
        'role_teacher': 'Teacher',
        'role_student': 'Student',
        'avg_grade': 'Average Grade',
        'success_rate': 'Success Rate %',
        'quality_rate': 'Quality Rate %',
        'total_students': 'Total Students',
        'at_risk': 'At Risk',
        'predicted_risk': 'Dropout Prediction',
        'heatmap': 'Problem Subjects',
        'search': 'Search...',
        'filter_group': 'Group',
        'filter_course': 'Course',
        'add': 'Add',
        'edit': 'Edit',
        'delete': 'Delete',
        'save': 'Save',
        'cancel': 'Cancel',
        'group': 'Group',
        'course': 'Course',
        'specialty': 'Specialty',
        'full_name': 'Full Name',
        'discipline': 'Discipline',
        'control_type': 'Control Type',
        'grade_value': 'Grade',
        'pass_fail': 'Pass/Fail',
        'passed': 'Passed',
        'not_passed': 'Failed',
        'date': 'Date',
        'semester': 'Semester',
        'action': 'Action',
        'logs': 'Logs',
        'theme': 'Theme',
        'language': 'Language',
        'change_password': 'Change Password',
        'old_password': 'Old Password',
        'new_password': 'New Password',
        'confirm_password': 'Confirm Password',
        'promote_to_teacher': 'Promote to Teacher',
        'reset_password': 'Reset Password',
        'error': 'Error',
        'success': 'Success',
        'confirm_delete': 'Are you sure?',
        'no_data': 'No data',
        'trend': 'Trend',
        'risk_probability': 'Risk Probability %',
        'comparison': 'Group Comparison',
        'select_group': 'Select Group',
        'compare': 'Compare',
        'top_students': 'Top Students',
        'group_ranking': 'Group Ranking',
    }
}


class LoginWindow(ctk.CTk):
    """Окно авторизации"""
    
    def __init__(self, on_login_success):
        super().__init__()
        
        self.on_login_success = on_login_success
        self.lang = 'ru'
        
        # Настройки окна
        self.title(TRANSLATIONS[self.lang]['login'])
        self.geometry("400x350")
        self.resizable(False, False)
        
        # Центрирование
        self.center_window()
        
        self.create_widgets()
    
    def center_window(self):
        """Центрирование окна"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Создание виджетов"""
        # Заголовок
        title_label = ctk.CTkLabel(
            self, 
            text="ПолесГУ", 
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(pady=(40, 10))
        
        subtitle = ctk.CTkLabel(
            self, 
            text="Система оценки успеваемости",
            font=ctk.CTkFont(size=14)
        )
        subtitle.pack(pady=(0, 30))
        
        # Фрейм для полей ввода
        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(padx=40, pady=10, fill="x")
        
        # Логин
        login_label = ctk.CTkLabel(form_frame, text=TRANSLATIONS[self.lang]['username'])
        login_label.pack(anchor="w", pady=(0, 5))
        self.login_entry = ctk.CTkEntry(form_frame, placeholder_text="admin")
        self.login_entry.pack(fill="x", pady=(0, 15))
        
        # Пароль
        password_label = ctk.CTkLabel(form_frame, text=TRANSLATIONS[self.lang]['password'])
        password_label.pack(anchor="w", pady=(0, 5))
        self.password_entry = ctk.CTkEntry(form_frame, show="*", placeholder_text="RwQNt")
        self.password_entry.pack(fill="x", pady=(0, 20))
        
        # Кнопка входа
        login_btn = ctk.CTkButton(
            form_frame, 
            text=TRANSLATIONS[self.lang]['login_btn'],
            command=self.try_login,
            height=40
        )
        login_btn.pack(fill="x")
        
        # Привязка Enter
        self.bind('<Return>', lambda e: self.try_login())
    
    def try_login(self):
        """Попытка входа"""
        login = self.login_entry.get().strip()
        password = self.password_entry.get()
        
        if not login or not password:
            messagebox.showerror(
                TRANSLATIONS[self.lang]['error'],
                "Заполните все поля"
            )
            return
        
        db = get_db_api()
        user = db.authenticate(login, password)
        
        if user:
            self.destroy()
            self.on_login_success(user)
        else:
            messagebox.showerror(
                TRANSLATIONS[self.lang]['error'],
                "Неверный логин или пароль"
            )
            self.password_entry.delete(0, 'end')


class MainWindow(ctk.CTk):
    """Главное окно приложения"""
    
    def __init__(self, user: Dict):
        super().__init__()
        
        self.user = user
        self.lang = 'ru'
        self.db = get_db_api()
        
        # Настройки окна
        self.title(TRANSLATIONS[self.lang]['title'])
        self.geometry("1200x800")
        
        # Состояние
        self.current_tab = None
        self.selected_group = None
        
        self.create_layout()
        self.load_dashboard()
    
    def create_layout(self):
        """Создание основной компоновки"""
        # Боковая панель
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        # Логотип и название
        logo_label = ctk.CTkLabel(
            self.sidebar,
            text="ПолесГУ",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        logo_label.pack(pady=(20, 5))
        
        # Информация о пользователе
        user_info = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        user_info.pack(pady=10, padx=10, fill="x")
        
        ctk.CTkLabel(
            user_info,
            text=self.user['full_name'],
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w"
        ).pack(fill="x")
        
        role_text = TRANSLATIONS[self.lang][f"role_{self.user['role']}"]
        ctk.CTkLabel(
            user_info,
            text=role_text,
            font=ctk.CTkFont(size=10),
            text_color="gray"
        ).pack(fill="x")
        
        # Разделитель
        ctk.CTkFrame(self.sidebar, height=2, fg_color="gray").pack(pady=10, padx=10, fill="x")
        
        # Кнопки навигации
        self.nav_buttons = {}
        self.create_nav_button('dashboard', '🏠')
        
        if self.user['role'] in ['admin', 'teacher']:
            self.create_nav_button('students', '🎓')
            self.create_nav_button('disciplines', '📚')
            self.create_nav_button('grades', '📝')
            self.create_nav_button('analytics', '📊')
        
        if self.user['role'] == 'admin':
            self.create_nav_button('users', '👥')
        
        self.create_nav_button('settings', '⚙️')
        
        # Разделитель
        ctk.CTkFrame(self.sidebar, height=2, fg_color="gray").pack(pady=10, padx=10, fill="x")
        
        # Кнопка выхода
        logout_btn = ctk.CTkButton(
            self.sidebar,
            text=TRANSLATIONS[self.lang]['logout'],
            command=self.logout,
            fg_color="red",
            hover_color="darkred"
        )
        logout_btn.pack(pady=10, padx=10, fill="x")
        
        # Основная область контента
        self.content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.content_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
    
    def create_nav_button(self, tab_name: str, icon: str):
        """Создание кнопки навигации"""
        btn = ctk.CTkButton(
            self.sidebar,
            text=f"{icon}  {TRANSLATIONS[self.lang][tab_name]}",
            command=lambda: self.switch_tab(tab_name),
            anchor="w",
            padx=20
        )
        btn.pack(pady=2, padx=10, fill="x")
        self.nav_buttons[tab_name] = btn
    
    def switch_tab(self, tab_name: str):
        """Переключение вкладок"""
        # Очистка текущего контента
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Подсветка активной кнопки
        for name, btn in self.nav_buttons.items():
            if name == tab_name:
                btn.configure(fg_color="#1f6aa5")
            else:
                btn.configure(fg_color="transparent")
        
        # Загрузка содержимого вкладки
        if tab_name == 'dashboard':
            self.load_dashboard()
        elif tab_name == 'students':
            self.load_students_tab()
        elif tab_name == 'disciplines':
            self.load_disciplines_tab()
        elif tab_name == 'grades':
            self.load_grades_tab()
        elif tab_name == 'analytics':
            self.load_analytics_tab()
        elif tab_name == 'users':
            self.load_users_tab()
        elif tab_name == 'settings':
            self.load_settings_tab()
    
    def load_dashboard(self):
        """Загрузка главной панели"""
        # Заголовок
        header = ctk.CTkLabel(
            self.content_frame,
            text=TRANSLATIONS[self.lang]['dashboard'],
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(anchor="w", pady=(0, 20))
        
        # Получение аналитики
        analytics = self.db.get_analytics()
        
        # KPI карточки
        kpi_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=(0, 20))
        
        kpis = [
            (TRANSLATIONS[self.lang]['avg_grade'], str(analytics['avg_grade']), "📈"),
            (TRANSLATIONS[self.lang]['success_rate'], f"{analytics['success_rate']}%", "✅"),
            (TRANSLATIONS[self.lang]['quality_rate'], f"{analytics['quality_rate']}%", "⭐"),
            (TRANSLATIONS[self.lang]['total_students'], str(analytics['total_students']), "👨‍🎓"),
        ]
        
        for i, (title, value, icon) in enumerate(kpis):
            card = ctk.CTkFrame(kpi_frame, width=200, height=100)
            card.grid(row=0, column=i, padx=10, pady=10)
            
            ctk.CTkLabel(
                card,
                text=icon,
                font=ctk.CTkFont(size=20)
            ).pack(pady=(10, 0))
            
            ctk.CTkLabel(
                card,
                text=value,
                font=ctk.CTkFont(size=28, weight="bold")
            ).pack()
            
            ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(size=12),
                text_color="gray"
            ).pack(pady=(0, 10))
        
        kpi_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # Графики и таблицы
        charts_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        charts_frame.pack(fill="both", expand=True)
        
        # Левая колонка - Тепловая карта
        left_col = ctk.CTkFrame(charts_frame, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        heatmap_title = ctk.CTkLabel(
            left_col,
            text=TRANSLATIONS[self.lang]['heatmap'],
            font=ctk.CTkFont(size=16, weight="bold")
        )
        heatmap_title.pack(anchor="w", pady=(0, 10))
        
        # Данные тепловой карты
        heatmap_data = self.db.get_heatmap_data()
        
        heatmap_scroll = ctk.CTkScrollableFrame(left_col)
        heatmap_scroll.pack(fill="both", expand=True)
        
        # Таблица тепловой карты
        headers = ["Предмет", "% проблемных оценок"]
        for i, header in enumerate(headers):
            ctk.CTkLabel(
                heatmap_scroll,
                text=header,
                font=ctk.CTkFont(weight="bold"),
                width=200
            ).grid(row=0, column=i, padx=5, pady=5, sticky="w")
        
        for row_idx, (discipline, poor_rate) in enumerate(heatmap_data.items(), 1):
            # Цвет в зависимости от процента
            if poor_rate > 20:
                color = "#ff4444"
            elif poor_rate > 10:
                color = "#ffaa00"
            else:
                color = "#44aa44"
            
            ctk.CTkLabel(
                heatmap_scroll,
                text=discipline[:40],
                width=200,
                anchor="w"
            ).grid(row=row_idx, column=0, padx=5, pady=3, sticky="w")
            
            ctk.CTkLabel(
                heatmap_scroll,
                text=f"{poor_rate}%",
                text_color=color,
                font=ctk.CTkFont(weight="bold"),
                width=100
            ).grid(row=row_idx, column=1, padx=5, pady=3, sticky="w")
        
        # Правая колонка - Группа риска
        right_col = ctk.CTkFrame(charts_frame, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        risk_title = ctk.CTkLabel(
            right_col,
            text=TRANSLATIONS[self.lang]['at_risk'],
            font=ctk.CTkFont(size=16, weight="bold")
        )
        risk_title.pack(anchor="w", pady=(0, 10))
        
        risk_scroll = ctk.CTkScrollableFrame(right_col)
        risk_scroll.pack(fill="both", expand=True)
        
        at_risk = self.db.get_at_risk_students(threshold=4)
        
        if at_risk:
            headers = ["ФИО", "Группа", "Ср. балл"]
            for i, header in enumerate(headers):
                ctk.CTkLabel(
                    risk_scroll,
                    text=header,
                    font=ctk.CTkFont(weight="bold"),
                    width=150
                ).grid(row=0, column=i, padx=5, pady=5, sticky="w")
            
            for row_idx, student in enumerate(at_risk, 1):
                ctk.CTkLabel(
                    risk_scroll,
                    text=student['full_name'][:25],
                    width=150,
                    anchor="w"
                ).grid(row=row_idx, column=0, padx=5, pady=3, sticky="w")
                
                ctk.CTkLabel(
                    risk_scroll,
                    text=student['group_name'],
                    width=80
                ).grid(row=row_idx, column=1, padx=5, pady=3, sticky="w")
                
                avg = student['avg_grade'] or 0
                color = "#ff4444" if avg < 4 else "#ffaa00"
                ctk.CTkLabel(
                    risk_scroll,
                    text=f"{avg:.2f}",
                    text_color=color,
                    width=80
                ).grid(row=row_idx, column=2, padx=5, pady=3, sticky="w")
        else:
            ctk.CTkLabel(
                risk_scroll,
                text=TRANSLATIONS[self.lang]['no_data'],
                text_color="gray"
            ).pack(pady=20)
        
        # Блок прогноза риска
        predict_frame = ctk.CTkFrame(self.content_frame)
        predict_frame.pack(fill="x", pady=(20, 0))
        
        predict_title = ctk.CTkLabel(
            predict_frame,
            text=TRANSLATIONS[self.lang]['predicted_risk'],
            font=ctk.CTkFont(size=16, weight="bold")
        )
        predict_title.pack(anchor="w", padx=10, pady=(10, 5))
        
        predict_scroll = ctk.CTkScrollableFrame(predict_frame, height=120)
        predict_scroll.pack(fill="x", padx=10, pady=(0, 10))
        
        predicted = self.db.get_predicted_risk_students()
        
        if predicted:
            headers = ["ФИО", "Группа", "Тренд", "Вероятность"]
            for i, header in enumerate(headers):
                ctk.CTkLabel(
                    predict_scroll,
                    text=header,
                    font=ctk.CTkFont(weight="bold"),
                    width=150
                ).grid(row=0, column=i, padx=5, pady=5, sticky="w")
            
            for row_idx, student in enumerate(predicted[:5], 1):
                ctk.CTkLabel(
                    predict_scroll,
                    text=student['full_name'][:20],
                    width=150,
                    anchor="w"
                ).grid(row=row_idx, column=0, padx=5, pady=3, sticky="w")
                
                ctk.CTkLabel(
                    predict_scroll,
                    text=student['group_name'],
                    width=80
                ).grid(row=row_idx, column=1, padx=5, pady=3, sticky="w")
                
                trend_color = "#ff4444" if student['trend'] < -15 else "#ffaa00"
                ctk.CTkLabel(
                    predict_scroll,
                    text=f"{student['trend']:.1f}%",
                    text_color=trend_color,
                    width=80
                ).grid(row=row_idx, column=2, padx=5, pady=3, sticky="w")
                
                risk_color = "#ff4444" if student['risk_probability'] > 70 else "#ffaa00"
                ctk.CTkLabel(
                    predict_scroll,
                    text=f"{student['risk_probability']:.0f}%",
                    text_color=risk_color,
                    font=ctk.CTkFont(weight="bold"),
                    width=80
                ).grid(row=row_idx, column=3, padx=5, pady=3, sticky="w")
        else:
            ctk.CTkLabel(
                predict_scroll,
                text="Студентов с высоким риском не выявлено",
                text_color="gray"
            ).pack(pady=10)
    
    def load_students_tab(self):
        """Вкладка студентов"""
        header = ctk.CTkLabel(
            self.content_frame,
            text=TRANSLATIONS[self.lang]['students'],
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(anchor="w", pady=(0, 20))
        
        # Панель фильтров
        filter_frame = ctk.CTkFrame(self.content_frame)
        filter_frame.pack(fill="x", pady=(0, 10))
        
        # Поиск
        ctk.CTkLabel(filter_frame, text=TRANSLATIONS[self.lang]['search']).grid(row=0, column=0, padx=5, pady=5)
        search_entry = ctk.CTkEntry(filter_frame, placeholder_text="ФИО...")
        search_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Группа
        ctk.CTkLabel(filter_frame, text=TRANSLATIONS[self.lang]['group']).grid(row=0, column=2, padx=5, pady=5)
        groups = self.db.get_available_groups()
        group_combo = ctk.CTkComboBox(filter_frame, values=["Все"] + groups)
        group_combo.grid(row=0, column=3, padx=5, pady=5)
        group_combo.set("Все")
        
        # Курс
        ctk.CTkLabel(filter_frame, text=TRANSLATIONS[self.lang]['course']).grid(row=0, column=4, padx=5, pady=5)
        course_combo = ctk.CTkComboBox(filter_frame, values=["Все", "1", "2", "3", "4"])
        course_combo.grid(row=0, column=5, padx=5, pady=5)
        course_combo.set("Все")
        
        # Кнопка применения
        def apply_filters():
            self.display_students_table(
                group_combo.get() if group_combo.get() != "Все" else None,
                int(course_combo.get()) if course_combo.get() != "Все" and course_combo.get().isdigit() else None,
                search_entry.get().strip() if search_entry.get().strip() else None
            )
        
        apply_btn = ctk.CTkButton(filter_frame, text="Применить", command=apply_filters)
        apply_btn.grid(row=0, column=6, padx=10, pady=5)
        
        # Таблица студентов
        self.students_table_frame = ctk.CTkFrame(self.content_frame)
        self.students_table_frame.pack(fill="both", expand=True)
        
        self.display_students_table()
    
    def display_students_table(self, group_filter=None, course_filter=None, search_query=None):
        """Отображение таблицы студентов"""
        # Очистка
        for widget in self.students_table_frame.winfo_children():
            widget.destroy()
        
        students = self.db.get_all_students(group_filter, course_filter, search_query)
        
        if not students:
            ctk.CTkLabel(
                self.students_table_frame,
                text=TRANSLATIONS[self.lang]['no_data'],
                text_color="gray"
            ).pack(pady=20)
            return
        
        # Scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(self.students_table_frame)
        scroll_frame.pack(fill="both", expand=True)
        
        # Заголовки
        headers = ["№", "ФИО", "Группа", "Курс", "Ср. балл"]
        for i, header in enumerate(headers):
            ctk.CTkLabel(
                scroll_frame,
                text=header,
                font=ctk.CTkFont(weight="bold"),
                width=150
            ).grid(row=0, column=i, padx=5, pady=5, sticky="w")
        
        # Строки
        for row_idx, student in enumerate(students, 1):
            ctk.CTkLabel(
                scroll_frame,
                text=str(row_idx),
                width=50
            ).grid(row=row_idx, column=0, padx=5, pady=3)
            
            ctk.CTkLabel(
                scroll_frame,
                text=student['full_name'],
                width=250,
                anchor="w"
            ).grid(row=row_idx, column=1, padx=5, pady=3, sticky="w")
            
            ctk.CTkLabel(
                scroll_frame,
                text=student['group_name'],
                width=100
            ).grid(row=row_idx, column=2, padx=5, pady=3)
            
            ctk.CTkLabel(
                scroll_frame,
                text=str(student['course']),
                width=50
            ).grid(row=row_idx, column=3, padx=5, pady=3)
            
            # Расчет среднего балла
            grades = self.db.get_student_grades(student['id'])
            numeric_grades = [g['value'] for g in grades if g['value'] is not None]
            avg = sum(numeric_grades) / len(numeric_grades) if numeric_grades else 0
            
            color = "#44aa44" if avg >= 7 else ("#ffaa00" if avg >= 4 else "#ff4444")
            ctk.CTkLabel(
                scroll_frame,
                text=f"{avg:.2f}",
                text_color=color,
                width=80
            ).grid(row=row_idx, column=4, padx=5, pady=3)
    
    def load_disciplines_tab(self):
        """Вкладка дисциплин"""
        header = ctk.CTkLabel(
            self.content_frame,
            text=TRANSLATIONS[self.lang]['disciplines'],
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(anchor="w", pady=(0, 20))
        
        disciplines = self.db.get_all_disciplines()
        
        scroll_frame = ctk.CTkScrollableFrame(self.content_frame)
        scroll_frame.pack(fill="both", expand=True)
        
        headers = ["№", "Предмет", "Кафедра", "Преподаватель"]
        for i, header in enumerate(headers):
            ctk.CTkLabel(
                scroll_frame,
                text=header,
                font=ctk.CTkFont(weight="bold"),
                width=200
            ).grid(row=0, column=i, padx=5, pady=5, sticky="w")
        
        for row_idx, disc in enumerate(disciplines, 1):
            ctk.CTkLabel(scroll_frame, text=str(row_idx), width=50).grid(row=row_idx, column=0, padx=5, pady=3)
            ctk.CTkLabel(scroll_frame, text=disc['name'], width=250, anchor="w").grid(row=row_idx, column=1, padx=5, pady=3, sticky="w")
            ctk.CTkLabel(scroll_frame, text=disc['department'], width=200).grid(row=row_idx, column=2, padx=5, pady=3)
            ctk.CTkLabel(scroll_frame, text=disc['teacher_name'] or "Не назначен", width=200).grid(row=row_idx, column=3, padx=5, pady=3)
    
    def load_grades_tab(self):
        """Вкладка журнала оценок"""
        header = ctk.CTkLabel(
            self.content_frame,
            text=TRANSLATIONS[self.lang]['grades'],
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(anchor="w", pady=(0, 20))
        
        # Выбор группы и предмета
        select_frame = ctk.CTkFrame(self.content_frame)
        select_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(select_frame, text=TRANSLATIONS[self.lang]['group']).grid(row=0, column=0, padx=5, pady=5)
        groups = self.db.get_available_groups()
        self.grade_group_combo = ctk.CTkComboBox(select_frame, values=groups)
        self.grade_group_combo.grid(row=0, column=1, padx=5, pady=5)
        if groups:
            self.grade_group_combo.set(groups[0])
        
        ctk.CTkLabel(select_frame, text=TRANSLATIONS[self.lang]['discipline']).grid(row=0, column=2, padx=5, pady=5)
        disciplines = self.db.get_all_disciplines()
        self.discipline_values = {d['name']: d['id'] for d in disciplines}
        self.grade_discipline_combo = ctk.CTkComboBox(select_frame, values=list(self.discipline_values.keys()))
        self.grade_discipline_combo.grid(row=0, column=3, padx=5, pady=5)
        if disciplines:
            self.grade_discipline_combo.set(disciplines[0]['name'])
        
        load_btn = ctk.CTkButton(select_frame, text="Загрузить", command=self.load_grade_journal)
        load_btn.grid(row=0, column=4, padx=10, pady=5)
        
        # Область журнала
        self.journal_frame = ctk.CTkFrame(self.content_frame)
        self.journal_frame.pack(fill="both", expand=True)
    
    def load_grade_journal(self):
        """Загрузка журнала оценок"""
        for widget in self.journal_frame.winfo_children():
            widget.destroy()
        
        group = self.grade_group_combo.get()
        discipline_name = self.grade_discipline_combo.get()
        discipline_id = self.discipline_values.get(discipline_name)
        
        if not discipline_id:
            return
        
        grades = self.db.get_grades_for_group(group, discipline_id)
        
        scroll_frame = ctk.CTkScrollableFrame(self.journal_frame)
        scroll_frame.pack(fill="both", expand=True)
        
        headers = ["№", "ФИО", "Оценка", "Тип", "Дата", "Действие"]
        for i, header in enumerate(headers):
            ctk.CTkLabel(
                scroll_frame,
                text=header,
                font=ctk.CTkFont(weight="bold"),
                width=120
            ).grid(row=0, column=i, padx=5, pady=5)
        
        for row_idx, record in enumerate(grades, 1):
            ctk.CTkLabel(scroll_frame, text=str(row_idx), width=50).grid(row=row_idx, column=0, padx=5, pady=3)
            ctk.CTkLabel(scroll_frame, text=record['full_name'], width=200, anchor="w").grid(row=row_idx, column=1, padx=5, pady=3, sticky="w")
            
            # Оценка или зачет
            if record['pass_fail']:
                grade_text = TRANSLATIONS[self.lang]['passed'] if record['pass_value'] else TRANSLATIONS[self.lang]['not_passed']
            else:
                grade_text = str(record['value']) if record['value'] else "-"
            
            ctk.CTkLabel(scroll_frame, text=grade_text, width=80).grid(row=row_idx, column=2, padx=5, pady=3)
            ctk.CTkLabel(scroll_frame, text=record['control_type'], width=120).grid(row=row_idx, column=3, padx=5, pady=3)
            ctk.CTkLabel(scroll_frame, text=record['date'], width=100).grid(row=row_idx, column=4, padx=5, pady=3)
            
            # Кнопка редактирования (только для преподавателя и админа)
            if self.user['role'] in ['admin', 'teacher']:
                edit_btn = ctk.CTkButton(
                    scroll_frame,
                    text=TRANSLATIONS[self.lang]['edit'],
                    width=80,
                    command=lambda r=record: self.edit_grade_dialog(r)
                )
                edit_btn.grid(row=row_idx, column=5, padx=5, pady=3)
    
    def edit_grade_dialog(self, record):
        """Диалог редактирования оценки"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(TRANSLATIONS[self.lang]['edit'])
        dialog.geometry("400x300")
        dialog.transient(self)
        
        ctk.CTkLabel(dialog, text=f"Студент: {record['full_name']}", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        ctk.CTkLabel(dialog, text=f"Тип: {record['control_type']}").pack(pady=5)
        
        # Поле оценки
        if record['pass_fail']:
            ctk.CTkLabel(dialog, text="Зачет").pack(pady=5)
            pass_var = ctk.BooleanVar(value=record['pass_value'])
            pass_check = ctk.CTkCheckBox(dialog, text=TRANSLATIONS[self.lang]['passed'], variable=pass_var)
            pass_check.pack(pady=10)
            
            def save_pass():
                self.db.update_grade(record['grade_id'], 0, self.user['id'], pass_var.get())
                messagebox.showinfo(TRANSLATIONS[self.lang]['success'], "Зачет обновлен")
                dialog.destroy()
                self.load_grade_journal()
            
            ctk.CTkButton(dialog, text=TRANSLATIONS[self.lang]['save'], command=save_pass).pack(pady=10)
        else:
            ctk.CTkLabel(dialog, text="Оценка (2-10)").pack(pady=5)
            grade_entry = ctk.CTkEntry(dialog, placeholder_text=str(record['value']))
            grade_entry.pack(pady=10)
            grade_entry.insert(0, str(record['value']) if record['value'] else "")
            
            def save_grade():
                try:
                    new_val = int(grade_entry.get())
                    if 2 <= new_val <= 10:
                        self.db.update_grade(record['grade_id'], new_val, self.user['id'])
                        messagebox.showinfo(TRANSLATIONS[self.lang]['success'], "Оценка обновлена")
                        dialog.destroy()
                        self.load_grade_journal()
                    else:
                        messagebox.showerror(TRANSLATIONS[self.lang]['error'], "Оценка должна быть от 2 до 10")
                except ValueError:
                    messagebox.showerror(TRANSLATIONS[self.lang]['error'], "Введите число")
            
            ctk.CTkButton(dialog, text=TRANSLATIONS[self.lang]['save'], command=save_grade).pack(pady=10)
        
        ctk.CTkButton(dialog, text=TRANSLATIONS[self.lang]['cancel'], command=dialog.destroy, fg_color="gray").pack(pady=5)
    
    def load_analytics_tab(self):
        """Вкладка аналитики"""
        header = ctk.CTkLabel(
            self.content_frame,
            text=TRANSLATIONS[self.lang]['analytics'],
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(anchor="w", pady=(0, 20))
        
        # Топ студентов
        top_frame = ctk.CTkFrame(self.content_frame)
        top_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            top_frame,
            text=TRANSLATIONS[self.lang]['top_students'],
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        top_students = self.db.get_top_students(10)
        
        top_scroll = ctk.CTkScrollableFrame(top_frame, height=200)
        top_scroll.pack(fill="x", padx=10, pady=(0, 10))
        
        for i, student in enumerate(top_students, 1):
            ctk.CTkLabel(
                top_scroll,
                text=f"{i}. {student['full_name']} ({student['group_name']}) - {student['avg_grade']:.2f}",
                anchor="w"
            ).pack(fill="x", padx=5, pady=2)
        
        # Рейтинг групп
        rank_frame = ctk.CTkFrame(self.content_frame)
        rank_frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            rank_frame,
            text=TRANSLATIONS[self.lang]['group_ranking'],
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        group_ranking = self.db.get_group_ranking()
        
        rank_scroll = ctk.CTkScrollableFrame(rank_frame)
        rank_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        for i, group in enumerate(group_ranking, 1):
            ctk.CTkLabel(
                rank_scroll,
                text=f"{i}. {group['group_name']} - Ср. балл: {group['avg_grade']:.2f} ({group['student_count']} студ.)",
                anchor="w"
            ).pack(fill="x", padx=5, pady=2)
    
    def load_users_tab(self):
        """Вкладка пользователей (только админ)"""
        header = ctk.CTkLabel(
            self.content_frame,
            text=TRANSLATIONS[self.lang]['users'],
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(anchor="w", pady=(0, 20))
        
        users = self.db.get_all_users()
        
        scroll_frame = ctk.CTkScrollableFrame(self.content_frame)
        scroll_frame.pack(fill="both", expand=True)
        
        headers = ["№", "ФИО", "Логин", "Роль", "Действия"]
        for i, header in enumerate(headers):
            ctk.CTkLabel(
                scroll_frame,
                text=header,
                font=ctk.CTkFont(weight="bold"),
                width=150
            ).grid(row=0, column=i, padx=5, pady=5, sticky="w")
        
        for row_idx, user in enumerate(users, 1):
            ctk.CTkLabel(scroll_frame, text=str(row_idx), width=50).grid(row=row_idx, column=0, padx=5, pady=3)
            ctk.CTkLabel(scroll_frame, text=user['full_name'], width=250, anchor="w").grid(row=row_idx, column=1, padx=5, pady=3, sticky="w")
            ctk.CTkLabel(scroll_frame, text=user['login'], width=150).grid(row=row_idx, column=2, padx=5, pady=3)
            
            role_text = TRANSLATIONS[self.lang][f"role_{user['role']}"]
            ctk.CTkLabel(scroll_frame, text=role_text, width=120).grid(row=row_idx, column=3, padx=5, pady=3)
            
            # Кнопки действий для студентов
            if user['role'] == 'student' and user['id'] != self.user['id']:
                promote_btn = ctk.CTkButton(
                    scroll_frame,
                    text=TRANSLATIONS[self.lang]['promote_to_teacher'],
                    width=150,
                    command=lambda uid=user['id']: self.promote_user(uid)
                )
                promote_btn.grid(row=row_idx, column=4, padx=5, pady=3)
                
                reset_btn = ctk.CTkButton(
                    scroll_frame,
                    text=TRANSLATIONS[self.lang]['reset_password'],
                    width=120,
                    fg_color="orange",
                    command=lambda uid=user['id']: self.reset_user_password(uid)
                )
                reset_btn.grid(row=row_idx, column=5, padx=5, pady=3)
    
    def promote_user(self, user_id):
        """Повышение пользователя до преподавателя"""
        if messagebox.askyesno("Подтверждение", "Повысить пользователя до преподавателя?"):
            if self.db.promote_to_teacher(user_id, self.user['id']):
                messagebox.showinfo(TRANSLATIONS[self.lang]['success'], "Пользователь повышен")
                self.load_users_tab()
            else:
                messagebox.showerror(TRANSLATIONS[self.lang]['error'], "Ошибка при повышении")
    
    def reset_user_password(self, user_id):
        """Сброс пароля пользователя"""
        if messagebox.askyesno("Подтверждение", "Сбросить пароль пользователю на 'password'?"):
            if self.db.reset_user_password(user_id, self.user['id']):
                messagebox.showinfo(TRANSLATIONS[self.lang]['success'], "Пароль сброшен")
            else:
                messagebox.showerror(TRANSLATIONS[self.lang]['error'], "Ошибка при сбросе")
    
    def load_settings_tab(self):
        """Вкладка настроек"""
        header = ctk.CTkLabel(
            self.content_frame,
            text=TRANSLATIONS[self.lang]['settings'],
            font=ctk.CTkFont(size=24, weight="bold")
        )
        header.pack(anchor="w", pady=(0, 20))
        
        # Профиль
        profile_frame = ctk.CTkFrame(self.content_frame)
        profile_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            profile_frame,
            text=TRANSLATIONS[self.lang]['profile'],
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=10)
        
        ctk.CTkLabel(profile_frame, text=f"ФИО: {self.user['full_name']}").pack(anchor="w", padx=20, pady=5)
        ctk.CTkLabel(profile_frame, text=f"Логин: {self.user['login']}").pack(anchor="w", padx=20, pady=5)
        ctk.CTkLabel(profile_frame, text=f"Роль: {TRANSLATIONS[self.lang][f'role_{self.user['role']}']}").pack(anchor="w", padx=20, pady=5)
        
        # Смена пароля
        password_frame = ctk.CTkFrame(self.content_frame)
        password_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            password_frame,
            text=TRANSLATIONS[self.lang]['change_password'],
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=10)
        
        form = ctk.CTkFrame(password_frame, fg_color="transparent")
        form.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(form, text=TRANSLATIONS[self.lang]['old_password']).grid(row=0, column=0, padx=5, pady=5)
        old_pass_entry = ctk.CTkEntry(form, show="*")
        old_pass_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(form, text=TRANSLATIONS[self.lang]['new_password']).grid(row=1, column=0, padx=5, pady=5)
        new_pass_entry = ctk.CTkEntry(form, show="*")
        new_pass_entry.grid(row=1, column=1, padx=5, pady=5)
        
        def change_password():
            old = old_pass_entry.get()
            new = new_pass_entry.get()
            
            if not old or not new:
                messagebox.showerror(TRANSLATIONS[self.lang]['error'], "Заполните все поля")
                return
            
            if self.db.change_password(self.user['id'], old, new):
                messagebox.showinfo(TRANSLATIONS[self.lang]['success'], "Пароль изменен")
                old_pass_entry.delete(0, 'end')
                new_pass_entry.delete(0, 'end')
            else:
                messagebox.showerror(TRANSLATIONS[self.lang]['error'], "Неверный старый пароль")
        
        ctk.CTkButton(form, text=TRANSLATIONS[self.lang]['save'], command=change_password).grid(row=2, column=1, padx=5, pady=10)
        
        # Тема
        theme_frame = ctk.CTkFrame(self.content_frame)
        theme_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            theme_frame,
            text=TRANSLATIONS[self.lang]['theme'],
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=10)
        
        theme_segmented = ctk.CTkSegmentedButton(
            theme_frame,
            values=["Dark", "Light", "System"],
            command=ctk.set_appearance_mode
        )
        theme_segmented.pack(padx=20, pady=10)
        theme_segmented.set("Dark")
        
        # Язык
        lang_frame = ctk.CTkFrame(self.content_frame)
        lang_frame.pack(fill="x")
        
        ctk.CTkLabel(
            lang_frame,
            text=TRANSLATIONS[self.lang]['language'],
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10, pady=10)
        
        lang_segmented = ctk.CTkSegmentedButton(
            lang_frame,
            values=["ru", "en"],
            command=self.change_language
        )
        lang_segmented.pack(padx=20, pady=10)
        lang_segmented.set("ru")
    
    def change_language(self, lang):
        """Смена языка"""
        self.lang = lang
        # Перезагрузка текущей вкладки
        if self.current_tab:
            self.switch_tab(self.current_tab)
    
    def logout(self):
        """Выход из системы"""
        if messagebox.askyesno("Выход", "Вы действительно хотите выйти?"):
            self.destroy()
            # Возврат к окну авторизации
            app = LoginWindow(lambda user: MainWindow(user))
            app.mainloop()


def run_client():
    """Запуск клиентского приложения"""
    # Инициализация сервера
    initialize_server()
    
    # Создание окна авторизации
    app = LoginWindow(lambda user: MainWindow(user))
    app.mainloop()


if __name__ == "__main__":
    run_client()
