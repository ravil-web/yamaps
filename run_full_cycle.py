#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Полный цикл: парсинг + статический HTML дашборд
"""

import sys
import os
import time
import webbrowser
from datetime import datetime

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from final_working_parser import FinalWorkingParser
from client_dashboard_generator import ClientDashboardGenerator
from config import TARGET_BUSINESSES_COUNT

def run_parsing():
    """Запуск парсинга"""
    print("🔍 ЭТАП 1: ПАРСИНГ ДАННЫХ")
    print("=" * 40)
    
    # Запрос имени проекта
    project_name = input("📝 Введите имя для этого проекта парсинга: ").strip()
    if not project_name:
        project_name = f"parsing_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"💡 Используется автоматическое имя: {project_name}")
    
    # URL для парсинга
    default_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/?ll=39.806284%2C47.275656&z=12"
    
    # Получаем URL от пользователя или используем по умолчанию
    url = input(f"🔗 Введите URL для парсинга (Enter для использования по умолчанию): ").strip()
    if not url:
        url = default_url
        print(f"💡 Используется URL по умолчанию: {url}")
    
    # Получаем количество предприятий
    try:
        default_value = str(TARGET_BUSINESSES_COUNT) if TARGET_BUSINESSES_COUNT > 0 else "все найденные"
        user_input = input(f"🎯 Введите количество предприятий для парсинга (по умолчанию {default_value}): ").strip()
        
        if not user_input:
            target_count = TARGET_BUSINESSES_COUNT
            print(f"💡 Используется значение из конфигурации: {default_value}")
        else:
            target_count = int(user_input)
    except ValueError:
        target_count = TARGET_BUSINESSES_COUNT
        print(f"⚠️ Используется значение из конфигурации: {default_value}")
    
    parser = FinalWorkingParser(target_count=target_count)
    
    try:
        # Запускаем парсинг
        success = parser.parse(url)
        
        if success:
            successful_count = len(parser.businesses)
            print(f"🎉 Парсинг завершен!")
            print(f"   ✅ Успешно: {successful_count} предприятий")
            print(f"   🎯 Цель: {target_count} предприятий")
            
            # Сохраняем результаты с именем проекта (дашборд создается автоматически)
            parser.save_results(project_name=project_name)
            
            return True, successful_count
        else:
            print("❌ Парсинг завершился с ошибками")
            return False, 0
        
    except KeyboardInterrupt:
        print("\n⏹️ Парсинг прерван пользователем")
        return False, 0
    except Exception as e:
        print(f"❌ Ошибка парсинга: {e}")
        return False, 0
    finally:
        parser.close()

def create_dashboard():
    """Создание HTML дашборда"""
    print("\n📊 ЭТАП 2: СОЗДАНИЕ ДАШБОРДА")
    print("=" * 40)
    
    try:
        # Ищем последний созданный JSON файл
        import glob
        json_files = glob.glob("output/*.json")
        
        if not json_files:
            print("❌ Не найдены JSON файлы для создания дашборда")
            return False, None
        
        # Берем самый новый файл
        latest_json = max(json_files, key=os.path.getctime)
        
        generator = ClientDashboardGenerator()
        
        print(f"🎨 Генерация клиентского HTML дашборда...")
        print(f"📄 Источник данных: {latest_json}")
        
        dashboard_file = generator.generate_dashboard(latest_json)
        
        if dashboard_file:
            print(f"✅ Клиентский дашборд создан: {dashboard_file}")
            print(f"📁 Дашборд размещен в папке проекта: {os.path.dirname(dashboard_file)}")
            
            return True, dashboard_file
        else:
            print("❌ Ошибка создания дашборда")
            return False, None
            
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    """Главная функция полного цикла"""
    print("=" * 60)
    print("🏥 ПОЛНЫЙ ЦИКЛ: ПАРСИНГ + HTML ДАШБОРД")
    print("=" * 60)
    
    start_time = time.time()
    
    print(f"🎯 Цель: настраивается пользователем")
    print(f"📄 Поиск: настраивается пользователем")
    print(f"📁 Результаты: папка output/")
    print(f"🌐 Дашборд: папка dashboard/ (в корне проекта)")
    print(f"⏰ Старт: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    
    try:
        # Этап 1: Парсинг
        parsing_success, parsed_count = run_parsing()
        
        if not parsing_success:
            print("\n❌ ЗАВЕРШЕНИЕ: Парсинг не удался")
            return
        
        # Этап 2: Дашборд
        dashboard_success, dashboard_file = create_dashboard()
        
        # Финальный отчет
        end_time = time.time()
        duration = int(end_time - start_time)
        
        print("\n" + "=" * 60)
        print("🎉 ПОЛНЫЙ ЦИКЛ ЗАВЕРШЕН!")
        print("=" * 60)
        
        print(f"⏱️ Время выполнения: {duration//60}м {duration%60}с")
        print(f"📊 Обработано предприятий: {parsed_count}")
        
        if dashboard_success and dashboard_file:
            print(f"📄 Дашборд: {dashboard_file}")
            
            # Предложение открыть дашборд
            choice = input(f"\n🌐 Открыть дашборд в браузере? (y/n): ").strip().lower()
            
            if choice in ['y', 'yes', 'да', 'д', '']:
                try:
                    full_path = os.path.abspath(dashboard_file)
                    webbrowser.open(f'file://{full_path}')
                    print(f"✅ Дашборд открыт в браузере")
                except Exception as e:
                    print(f"⚠️ Не удалось открыть браузер: {e}")
                    print(f"💡 Откройте файл вручную: {dashboard_file}")
            else:
                print(f"💡 Дашборд готов: {dashboard_file}")
        
        print(f"\n📋 Результаты сохранены в: output/")
        print(f"🌐 Дашборд сохранен в: dashboard/")
        print(f"🎯 Миссия выполнена!")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ Процесс прерван пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
