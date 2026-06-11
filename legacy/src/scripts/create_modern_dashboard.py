#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Быстрое создание современного HTML дашборда из JSON файлов парсинга
"""

import sys
import os

# Добавляем корневую директорию проекта в путь поиска модулей
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
sys.path.append(project_root)

from src.dashboard.modern_dashboard import ModernDashboardGenerator

def main():
    """Основная функция"""
    if len(sys.argv) > 1:
        # Если указан файл как аргумент
        json_file = sys.argv[1]
        if not os.path.exists(json_file):
            print(f"❌ Файл не найден: {json_file}")
            return
        json_files_to_process = [json_file]
    else:
        # Ищем JSON файлы в output
        import glob
        json_files = glob.glob("output/*.json")
        
        if not json_files:
            print("❌ Не найдены JSON файлы в папке output/")
            print("Запустите парсер или укажите путь к JSON файлу")
            return
        
        # Показываем список файлов
        print("📁 Найденные JSON файлы:")
        for i, file in enumerate(json_files, 1):
            print(f"   {i}. {file}")
        
        try:
            choice = int(input("\nВыберите номер файла (или 0 для всех): "))
            if choice == 0:
                json_files_to_process = json_files
            elif 1 <= choice <= len(json_files):
                json_files_to_process = [json_files[choice - 1]]
            else:
                print("❌ Неверный номер")
                return
        except ValueError:
            print("❌ Введите число")
            return
    
    generator = ModernDashboardGenerator()
    
    for json_file in json_files_to_process:
        print(f"\n📊 Создание современного дашборда для: {json_file}")
        dashboard_file = generator.generate_dashboard(json_file)
        
        if dashboard_file:
            print(f"✅ Современный дашборд создан: {dashboard_file}")
            print(f"🌐 Откройте в браузере: {os.path.abspath(dashboard_file)}")
            print(f"📁 Дашборд сохранен в папке парсинга: {os.path.dirname(dashboard_file)}")

if __name__ == "__main__":
    main()
