#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для создания дашборда для конкретной сессии парсинга
"""

import os
import sys
from client_dashboard import ClientDashboardGenerator

def create_dashboard_for_session(session_name):
    """Создание дашборда для конкретной сессии"""
    
    # Путь к папке сессии
    session_folder = f"parsing_results/{session_name}"
    
    # Проверяем, существует ли папка
    if not os.path.exists(session_folder):
        print(f"❌ Папка сессии не найдена: {session_folder}")
        return False
    
    # Проверяем, есть ли данные предприятий
    businesses_folder = f"{session_folder}/businesses"
    if not os.path.exists(businesses_folder):
        print(f"❌ Папка с данными предприятий не найдена: {businesses_folder}")
        return False
    
    try:
        print(f"📊 Создание дашборда для сессии: {session_name}")
        print(f"📁 Папка сессии: {session_folder}")
        
        # Создаем генератор дашборда
        dashboard_generator = ClientDashboardGenerator(session_folder=session_folder)
        
        # Генерируем HTML дашборд
        dashboard_file = dashboard_generator.generate_html_dashboard()
        
        print(f"✅ Дашборд создан: {dashboard_file}")
        print("🌐 Откройте файл в браузере для просмотра")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания дашборда: {e}")
        return False

def main():
    """Главная функция"""
    
    if len(sys.argv) != 2:
        print("Использование: python create_dashboard_for_session.py <имя_сессии>")
        print("\nДоступные сессии:")
        
        # Показываем доступные папки сессий
        if os.path.exists("parsing_results"):
            for item in os.listdir("parsing_results"):
                session_path = f"parsing_results/{item}"
                if os.path.isdir(session_path) and os.path.exists(f"{session_path}/businesses"):
                    print(f"  - {item}")
        
        return
    
    session_name = sys.argv[1]
    
    # Создаем дашборд
    success = create_dashboard_for_session(session_name)
    
    if success:
        print("\n🎉 Дашборд успешно создан!")
    else:
        print("\n💥 Не удалось создать дашборд")

if __name__ == "__main__":
    main()
