#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Универсальный запуск парсеров Яндекс.Карт и Ozon
"""

import sys
import os
import time
from datetime import datetime

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    """Вывод баннера"""
    print("=" * 70)
    print("🚀 УНИВЕРСАЛЬНЫЙ ПАРСЕР")
    print("=" * 70)
    print("Доступные парсеры:")
    print("  🗺️  Яндекс.Карты - парсинг предприятий")
    print("  🛒 Ozon - парсинг товаров")
    print("  📊 Дашборды для всех платформ")
    print("=" * 70)

def show_menu():
    """Показать главное меню"""
    print("\n📋 ГЛАВНОЕ МЕНЮ")
    print("-" * 30)
    print("1. 🗺️  Парсер Яндекс.Карт")
    print("2. 🛒 Парсер Ozon")
    print("3. 🧪 Тесты парсеров")
    print("4. 📊 Просмотр дашбордов")
    print("5. ⚙️  Настройки")
    print("0. 🚪 Выход")

def run_yandex_parser():
    """Запуск парсера Яндекс.Карт"""
    print("\n🗺️ ПАРСЕР YANDEX.КАРТ")
    print("=" * 30)
    
    try:
        # Импортируем и запускаем парсер Яндекс.Карт
        from final_working_parser import FinalWorkingParser
        from config import SEARCH_URL, TARGET_BUSINESSES_COUNT
        
        print(f"🌐 URL для поиска: {SEARCH_URL[:80]}...")
        print(f"📊 Целевое количество предприятий: {TARGET_BUSINESSES_COUNT if TARGET_BUSINESSES_COUNT > 0 else 'все найденные'}")
        
        confirm = input("\nЗапустить парсинг Яндекс.Карт? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes', 'да', 'д']:
            print("❌ Парсинг отменен")
            return
        
        print("\n🚀 Запуск парсера Яндекс.Карт...")
        parser = FinalWorkingParser()
        
        # Запускаем парсинг
        businesses = parser.parse_businesses(SEARCH_URL)
        
        if businesses:
            print(f"\n✅ Парсинг завершен! Найдено {len(businesses)} предприятий")
            
            # Предложение создать дашборд
            create_dashboard = input("\nСоздать дашборд? (y/n): ").strip().lower()
            if create_dashboard in ['y', 'yes', 'да', 'д']:
                try:
                    from dashboard_generator import DashboardGenerator
                    generator = DashboardGenerator()
                    dashboard_data = {
                        'businesses': businesses,
                        'total_count': len(businesses),
                        'target_count': TARGET_BUSINESSES_COUNT,
                        'success_rate': (len(businesses) / TARGET_BUSINESSES_COUNT * 100) if TARGET_BUSINESSES_COUNT > 0 else 100,
                        'session_id': parser.session_id,
                        'search_url': SEARCH_URL,
                        'platform': 'Yandex Maps'
                    }
                    dashboard_file = generator.generate_dashboard(dashboard_data)
                    if dashboard_file:
                        print(f"✅ Дашборд создан: {dashboard_file}")
                except Exception as e:
                    print(f"❌ Ошибка создания дашборда: {e}")
        else:
            print("❌ Предприятия не найдены")
    
    except ImportError as e:
        print(f"❌ Ошибка импорта парсера Яндекс.Карт: {e}")
    except Exception as e:
        print(f"❌ Ошибка парсинга Яндекс.Карт: {e}")

def run_ozon_parser():
    """Запуск парсера Ozon"""
    print("\n🛒 ПАРСЕР OZON")
    print("=" * 30)
    
    try:
        # Импортируем и запускаем парсер Ozon
        from run_ozon_with_dashboard import main as run_ozon_main
        
        print("🚀 Запуск парсера Ozon с дашбордом...")
        run_ozon_main()
    
    except ImportError as e:
        print(f"❌ Ошибка импорта парсера Ozon: {e}")
    except Exception as e:
        print(f"❌ Ошибка парсинга Ozon: {e}")

def run_tests():
    """Запуск тестов"""
    print("\n🧪 ТЕСТЫ ПАРСЕРОВ")
    print("=" * 30)
    
    print("Выберите тесты для запуска:")
    print("1. Тесты парсера Яндекс.Карт")
    print("2. Тесты парсера Ozon")
    print("3. Все тесты")
    print("0. Назад")
    
    choice = input("\nВведите номер (0-3): ").strip()
    
    if choice == "1":
        try:
            from test_final_parser import main as test_yandex_main
            test_yandex_main()
        except ImportError:
            print("❌ Тесты парсера Яндекс.Карт не найдены")
    elif choice == "2":
        try:
            from test_ozon_integrated import main as test_ozon_main
            test_ozon_main()
        except ImportError:
            print("❌ Тесты парсера Ozon не найдены")
    elif choice == "3":
        print("🔄 Запуск всех тестов...")
        # Запускаем тесты Ozon (они более полные)
        try:
            from test_ozon_integrated import run_all_tests
            run_all_tests()
        except ImportError:
            print("❌ Тесты не найдены")
    elif choice == "0":
        return
    else:
        print("❌ Неверный выбор")

def view_dashboards():
    """Просмотр дашбордов"""
    print("\n📊 ПРОСМОТР ДАШБОРДОВ")
    print("=" * 30)
    
    dashboard_dir = "dashboard"
    if not os.path.exists(dashboard_dir):
        print("❌ Папка дашбордов не найдена")
        return
    
    # Ищем HTML файлы дашбордов
    dashboard_files = []
    for file in os.listdir(dashboard_dir):
        if file.endswith('.html'):
            dashboard_files.append(file)
    
    if not dashboard_files:
        print("❌ Дашборды не найдены")
        return
    
    print(f"📋 Найдено {len(dashboard_files)} дашбордов:")
    for i, file in enumerate(dashboard_files, 1):
        file_path = os.path.join(dashboard_dir, file)
        file_size = os.path.getsize(file_path)
        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        print(f"   {i}. {file}")
        print(f"      📊 Размер: {file_size} байт")
        print(f"      📅 Создан: {mod_time.strftime('%d.%m.%Y %H:%M')}")
    
    try:
        choice = input(f"\nВыберите дашборд для открытия (1-{len(dashboard_files)}, 0 - назад): ").strip()
        choice_num = int(choice)
        
        if choice_num == 0:
            return
        elif 1 <= choice_num <= len(dashboard_files):
            selected_file = dashboard_files[choice_num - 1]
            file_path = os.path.abspath(os.path.join(dashboard_dir, selected_file))
            
            print(f"🌐 Открытие дашборда: {selected_file}")
            
            try:
                import webbrowser
                webbrowser.open(f"file://{file_path}")
                print("✅ Дашборд открыт в браузере")
            except Exception as e:
                print(f"❌ Ошибка открытия дашборда: {e}")
                print(f"📁 Откройте файл вручную: {file_path}")
        else:
            print("❌ Неверный выбор")
    except ValueError:
        print("❌ Неверный формат номера")

def show_settings():
    """Показать настройки"""
    print("\n⚙️ НАСТРОЙКИ")
    print("=" * 30)
    
    try:
        from config import (
            TARGET_BUSINESSES_COUNT,
            TARGET_OZON_PRODUCTS_COUNT,
            SEARCH_URL,
            OZON_URLS
        )
        
        print("📊 Текущие настройки:")
        print(f"   🗺️  Яндекс.Карты - целевое количество: {TARGET_BUSINESSES_COUNT if TARGET_BUSINESSES_COUNT > 0 else 'все найденные'}")
        print(f"   🛒 Ozon - целевое количество: {TARGET_OZON_PRODUCTS_COUNT if TARGET_OZON_PRODUCTS_COUNT > 0 else 'все найденные'}")
        print(f"   🌐 URL Яндекс.Карт: {SEARCH_URL[:60]}...")
        print(f"   🌐 URL Ozon: {len(OZON_URLS)} доступных")
        
        print("\n📋 Доступные URL Ozon:")
        for key, url in OZON_URLS.items():
            print(f"   • {key}: {url[:50]}...")
        
        print("\n💡 Для изменения настроек отредактируйте файл config.py")
        
    except ImportError as e:
        print(f"❌ Ошибка загрузки настроек: {e}")

def main():
    """Основная функция"""
    print_banner()
    
    while True:
        show_menu()
        
        choice = input("\nВведите номер (0-5): ").strip()
        
        if choice == "0":
            print("\n👋 До свидания!")
            break
        elif choice == "1":
            run_yandex_parser()
        elif choice == "2":
            run_ozon_parser()
        elif choice == "3":
            run_tests()
        elif choice == "4":
            view_dashboards()
        elif choice == "5":
            show_settings()
        else:
            print("❌ Неверный выбор. Попробуйте снова.")
        
        input("\nНажмите Enter для продолжения...")

if __name__ == "__main__":
    main()