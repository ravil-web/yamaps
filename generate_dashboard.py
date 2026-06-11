#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Отдельный скрипт для генерации HTML дашборда
"""

import sys
import os
import argparse
from datetime import datetime

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.dashboard.static_dashboard import StaticDashboardGenerator
from src.config import *

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Генератор HTML дашборда для результатов парсинга')
    
    parser.add_argument('--output', '-o', 
                       help='Имя выходного HTML файла (по умолчанию dashboard_YYYYMMDD_HHMMSS.html)')
    parser.add_argument('--open', '-b', action='store_true',
                       help='Автоматически открыть дашборд в браузере')
    parser.add_argument('--session', '-s',
                       help='Имя сессии парсинга (папка внутри parsing_results)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🏥 ГЕНЕРАТОР HTML ДАШБОРДА")
    print("=" * 60)
    
    # Определяем источник данных
    if args.session:
        session_folder = f"{FOLDER_STRUCTURE['base_folder']}/{args.session}"
        if not os.path.exists(session_folder):
            print(f"❌ Сессия не найдена: {session_folder}")
            # Показываем доступные сессии
            main_folder = FOLDER_STRUCTURE['base_folder']
            if os.path.exists(main_folder):
                sessions = [d for d in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder, d))]
                if sessions:
                    print("📁 Доступные сессии:")
                    for session in sessions:
                        print(f"   - {session}")
                else:
                    print("📁 Нет доступных сессий")
            return
        data_source = session_folder
        print(f"📊 Сессия: {args.session}")
    else:
        # Интерактивный выбор сессии
        main_folder = FOLDER_STRUCTURE['base_folder']
        if not os.path.exists(main_folder):
            print(f"❌ Папка с данными не найдена: {main_folder}")
            print("💡 Сначала запустите парсинг: python main.py")
            return
        
        sessions = [d for d in os.listdir(main_folder) if os.path.isdir(os.path.join(main_folder, d))]
        if not sessions:
            print("❌ Нет сессий парсинга")
            print("💡 Сначала запустите парсинг: python main.py")
            return
        
        print("📁 Доступные сессии:")
        for i, session in enumerate(sessions, 1):
            print(f"   {i}. {session}")
        
        choice = input(f"\nВыберите сессию (1-{len(sessions)}): ").strip()
        try:
            session_idx = int(choice) - 1
            if 0 <= session_idx < len(sessions):
                selected_session = sessions[session_idx]
                data_source = f"{main_folder}/{selected_session}"
                print(f"📊 Выбрана сессия: {selected_session}")
            else:
                print("❌ Неверный выбор")
                return
        except ValueError:
            print("❌ Неверный формат")
            return
    
    # Определяем имя файла
    if args.output:
        output_file = args.output
        if not output_file.endswith('.html'):
            output_file += '.html'
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"dashboard_{timestamp}.html"
    
    print(f"📊 Создание дашборда...")
    print(f"📁 Источник данных: {data_source}")
    print(f"📄 Выходной файл: {output_file}")
    print("-" * 40)
    
    # Создание дашборда
    generator = StaticDashboardGenerator(session_folder=data_source)
    
    try:
        success = generator.generate_dashboard(output_file)
        
        if success:
            print("\n" + "=" * 40)
            print("🎉 ДАШБОРД ГОТОВ!")
            print("=" * 40)
            print(f"📄 Файл: {output_file}")
            print(f"📊 Данные: {len(generator.businesses_data)} предприятий")
            print(f"🛍️ Услуги: {len(generator.products_data)} товаров/услуг")
            
            # Автоматическое открытие в браузере
            if args.open:
                try:
                    import webbrowser
                    full_path = os.path.abspath(output_file)
                    webbrowser.open(f'file://{full_path}')
                    print(f"🌐 Дашборд открыт в браузере")
                except Exception as e:
                    print(f"⚠️ Не удалось открыть браузер: {e}")
            else:
                print(f"💡 Для просмотра откройте файл в браузере")
            
        else:
            print("\n❌ Ошибка создания дашборда")
            
    except KeyboardInterrupt:
        print("\n⏹️ Создание дашборда прервано пользователем")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")

if __name__ == "__main__":
    main()
