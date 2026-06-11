#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Быстрое создание клиентского HTML дашборда из JSON файлов парсинга
"""

import sys
import os

# Добавляем корневую директорию проекта в путь поиска модулей
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

from src.dashboard.client_dashboard import ClientDashboardGenerator

def main():
    """Основная функция"""
    from src.config import FOLDER_STRUCTURE
    
    # Путь к результатам парсинга
    base_folder = FOLDER_STRUCTURE['base_folder']
    
    if len(sys.argv) > 1:
        # Если передан путь к папке сессии
        session_folder = sys.argv[1]
        if not os.path.exists(session_folder):
             print(f"❌ Папка не найдена: {session_folder}")
             return
        
        generator = ClientDashboardGenerator(session_folder=session_folder)
        generator.generate_html_dashboard()
        
    else:
        # Ищем сессии в папке parsing_results
        if not os.path.exists(base_folder):
             print(f"❌ Папка с результатами не найдена: {base_folder}")
             return
             
        sessions = [d for d in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, d)) and d != 'logs']
        sessions.sort(reverse=True) # Самые новые сверху
        
        if not sessions:
            print(f"❌ Не найдено сессий парсинга в {base_folder}")
            return
        
        print(f"📁 Найденные сессии (в {base_folder}):")
        for i, session in enumerate(sessions, 1):
            print(f"   {i}. {session}")
            
        try:
            choice = input("\nВыберите номер сессии (или Enter для самой новой): ").strip()
            if not choice:
                session_name = sessions[0]
            else:
                idx = int(choice) - 1
                if 0 <= idx < len(sessions):
                    session_name = sessions[idx]
                else:
                    print("❌ Неверный номер")
                    return
            
            session_folder = os.path.join(base_folder, session_name)
            print(f"📊 Генерация дашборда для: {session_name}")
            
            generator = ClientDashboardGenerator(session_folder=session_folder)
            generator.generate_html_dashboard()
            
        except ValueError:
            print("❌ Неверный ввод")
            return

if __name__ == "__main__":
    main()
