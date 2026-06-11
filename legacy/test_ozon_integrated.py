#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тесты для интегрированного парсера Ozon
"""

import sys
import os
import time
import json
from datetime import datetime

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ozon_parser_integrated import OzonParserIntegrated
from ozon_dashboard_generator import OzonDashboardGenerator
from config import TARGET_OZON_PRODUCTS_COUNT, OZON_URLS

def test_parser_initialization():
    """Тест инициализации парсера"""
    print("🧪 ТЕСТ: Инициализация парсера")
    print("-" * 30)
    
    try:
        parser = OzonParserIntegrated(target_count=10)
        
        # Проверяем основные атрибуты
        assert parser.target_count == 10, "Неверное целевое количество"
        assert parser.products == [], "Список товаров должен быть пустым"
        assert parser.processed_urls == set(), "Обработанные URL должны быть пустыми"
        assert parser.session_id is not None, "ID сессии должен быть создан"
        
        print("✅ Парсер инициализирован корректно")
        print(f"   📊 Целевое количество: {parser.target_count}")
        print(f"   🆔 ID сессии: {parser.session_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return False

def test_driver_setup():
    """Тест настройки драйвера"""
    print("\n🧪 ТЕСТ: Настройка драйвера")
    print("-" * 30)
    
    try:
        parser = OzonParserIntegrated(target_count=5)
        
        # Тестируем настройку драйвера
        success = parser.setup_driver()
        
        if success:
            print("✅ Драйвер настроен успешно")
            print(f"   🌐 URL: {parser.driver.current_url}")
            print(f"   📏 Размер окна: {parser.driver.get_window_size()}")
            
            # Закрываем драйвер
            parser.close_driver()
            print("🔒 Драйвер закрыт")
            return True
        else:
            print("❌ Ошибка настройки драйвера")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования драйвера: {e}")
        return False

def test_url_validation():
    """Тест валидации URL"""
    print("\n🧪 ТЕСТ: Валидация URL")
    print("-" * 30)
    
    test_urls = [
        ("https://www.ozon.ru/seller/test-seller/", True),
        ("https://www.ozon.ru/search/?text=test", True),
        ("https://www.ozon.ru/category/test-123/", True),
        ("https://example.com/", False),
        ("invalid-url", False),
        ("", False)
    ]
    
    parser = OzonParserIntegrated()
    
    for url, expected in test_urls:
        try:
            # Простая проверка URL
            is_valid = url.startswith(('http://', 'https://')) and 'ozon.ru' in url
            result = is_valid == expected
            
            status = "✅" if result else "❌"
            print(f"   {status} {url[:50]}... -> {is_valid}")
            
        except Exception as e:
            print(f"   ❌ {url[:50]}... -> Ошибка: {e}")
    
    return True

def test_data_extraction():
    """Тест извлечения данных (мок-тест)"""
    print("\n🧪 ТЕСТ: Извлечение данных")
    print("-" * 30)
    
    try:
        parser = OzonParserIntegrated()
        
        # Создаем мок-данные для тестирования
        mock_products = [
            {
                'name': 'Тестовый товар 1',
                'price': '1234',
                'rating': '4.8 • 123 отзыва',
                'reviews': '4.8 • 123 отзыва',
                'link': 'https://www.ozon.ru/product/test1/',
                'delivery': 'Завтра',
                'address': 'Завтра',
                'phone': 'Не указан',
                'website': 'https://www.ozon.ru/product/test1/',
                'working_hours': 'Не указаны',
                'description': 'Тестовый товар 1'
            },
            {
                'name': 'Тестовый товар 2',
                'price': '5678',
                'rating': '4.5 • 89 отзывов',
                'reviews': '4.5 • 89 отзывов',
                'link': 'https://www.ozon.ru/product/test2/',
                'delivery': 'Сегодня',
                'address': 'Сегодня',
                'phone': 'Не указан',
                'website': 'https://www.ozon.ru/product/test2/',
                'working_hours': 'Не указаны',
                'description': 'Тестовый товар 2'
            }
        ]
        
        # Проверяем структуру данных
        for i, product in enumerate(mock_products, 1):
            required_fields = ['name', 'price', 'rating', 'reviews', 'link', 'delivery']
            
            for field in required_fields:
                assert field in product, f"Отсутствует поле {field} в товаре {i}"
                assert product[field] is not None, f"Поле {field} пустое в товаре {i}"
            
            print(f"   ✅ Товар {i}: {product['name'][:30]}...")
        
        print(f"✅ Все {len(mock_products)} товаров имеют корректную структуру")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования данных: {e}")
        return False

def test_dashboard_generation():
    """Тест генерации дашборда"""
    print("\n🧪 ТЕСТ: Генерация дашборда")
    print("-" * 30)
    
    try:
        generator = OzonDashboardGenerator()
        
        # Тестовые данные для дашборда
        test_data = {
            'products': [
                {
                    'name': 'Тестовый товар для дашборда',
                    'price': '9999',
                    'rating': '5.0 • 1 отзыв',
                    'reviews': '5.0 • 1 отзыв',
                    'delivery': 'Завтра',
                    'link': 'https://www.ozon.ru/product/test/'
                }
            ],
            'total_count': 1,
            'target_count': 10,
            'success_rate': 10.0,
            'session_id': 'test_20241208_120000',
            'search_url': 'https://www.ozon.ru/seller/test-seller/',
            'platform': 'Ozon'
        }
        
        # Генерируем дашборд
        dashboard_file = generator.generate_dashboard(test_data, "test_dashboard.html")
        
        if dashboard_file and os.path.exists(dashboard_file):
            print(f"✅ Дашборд создан: {dashboard_file}")
            
            # Проверяем размер файла
            file_size = os.path.getsize(dashboard_file)
            print(f"   📊 Размер файла: {file_size} байт")
            
            # Проверяем содержимое
            with open(dashboard_file, 'r', encoding='utf-8') as f:
                content = f.read()
                assert 'Тестовый товар для дашборда' in content, "Товар не найден в дашборде"
                assert '9999' in content, "Цена не найдена в дашборде"
                assert 'Ozon' in content, "Платформа не найдена в дашборде"
            
            print("✅ Содержимое дашборда корректно")
            
            # Удаляем тестовый файл
            os.remove(dashboard_file)
            print("🗑️ Тестовый файл удален")
            
            return True
        else:
            print("❌ Дашборд не создан")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования дашборда: {e}")
        return False

def test_configuration():
    """Тест конфигурации"""
    print("\n🧪 ТЕСТ: Конфигурация")
    print("-" * 30)
    
    try:
        # Проверяем импорт конфигурации
        from config import (
            TARGET_OZON_PRODUCTS_COUNT,
            OZON_URLS,
            OZON_DELAYS,
            OZON_BROWSER_OPTIONS,
            OZON_FOLDER_STRUCTURE,
            OZON_SAVE_OPTIONS,
            OZON_ERROR_HANDLING
        )
        
        # Проверяем основные настройки
        assert TARGET_OZON_PRODUCTS_COUNT >= 0, "Неверное целевое количество товаров"
        assert isinstance(OZON_URLS, dict), "URL должны быть в виде словаря"
        assert isinstance(OZON_DELAYS, dict), "Задержки должны быть в виде словаря"
        assert isinstance(OZON_BROWSER_OPTIONS, dict), "Настройки браузера должны быть в виде словаря"
        
        print("✅ Конфигурация загружена корректно")
        print(f"   📊 Целевое количество товаров: {TARGET_OZON_PRODUCTS_COUNT}")
        print(f"   🌐 Количество URL: {len(OZON_URLS)}")
        print(f"   ⏱️ Количество настроек задержек: {len(OZON_DELAYS)}")
        
        # Проверяем URL
        print("\n📋 Доступные URL:")
        for key, url in OZON_URLS.items():
            print(f"   • {key}: {url[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования конфигурации: {e}")
        return False

def test_save_results():
    """Тест сохранения результатов"""
    print("\n🧪 ТЕСТ: Сохранение результатов")
    print("-" * 30)
    
    try:
        parser = OzonParserIntegrated(target_count=5)
        
        # Создаем тестовые данные
        test_products = [
            {
                'name': 'Тестовый товар для сохранения',
                'price': '5555',
                'rating': '4.7 • 50 отзывов',
                'reviews': '4.7 • 50 отзывов',
                'link': 'https://www.ozon.ru/product/save-test/',
                'delivery': 'Завтра',
                'address': 'Завтра',
                'phone': 'Не указан',
                'website': 'https://www.ozon.ru/product/save-test/',
                'working_hours': 'Не указаны',
                'description': 'Тестовый товар для сохранения'
            }
        ]
        
        parser.products = test_products
        parser.search_url = "https://www.ozon.ru/seller/test-seller/"
        
        # Сохраняем результаты
        parser.save_results()
        
        # Проверяем создание папки сессии
        session_dir = f"parsing_results/session_{parser.session_id}"
        if os.path.exists(session_dir):
            print(f"✅ Папка сессии создана: {session_dir}")
            
            # Проверяем JSON файл
            json_file = f"{session_dir}/ozon_products.json"
            if os.path.exists(json_file):
                print(f"✅ JSON файл создан: {json_file}")
                
                # Проверяем содержимое JSON
                with open(json_file, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
                    assert len(saved_data) == 1, "Неверное количество товаров в JSON"
                    assert saved_data[0]['name'] == 'Тестовый товар для сохранения', "Неверное название товара"
                
                print("✅ Содержимое JSON корректно")
            else:
                print("❌ JSON файл не создан")
            
            # Проверяем Excel файл
            excel_file = f"output/ozon_products_{parser.session_id}.xlsx"
            if os.path.exists(excel_file):
                print(f"✅ Excel файл создан: {excel_file}")
            else:
                print("❌ Excel файл не создан")
            
            # Проверяем сводку
            summary_file = f"{session_dir}/summary.txt"
            if os.path.exists(summary_file):
                print(f"✅ Сводка создана: {summary_file}")
                
                # Проверяем содержимое сводки
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary_content = f.read()
                    assert 'Парсинг Ozon' in summary_content, "Заголовок не найден в сводке"
                    assert 'Найдено товаров: 1' in summary_content, "Количество товаров не найдено в сводке"
                
                print("✅ Содержимое сводки корректно")
            else:
                print("❌ Сводка не создана")
            
            return True
        else:
            print("❌ Папка сессии не создана")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка тестирования сохранения: {e}")
        return False

def run_all_tests():
    """Запуск всех тестов"""
    print("🚀 ЗАПУСК ВСЕХ ТЕСТОВ ПАРСЕРА OZON")
    print("=" * 50)
    
    tests = [
        ("Инициализация парсера", test_parser_initialization),
        ("Настройка драйвера", test_driver_setup),
        ("Валидация URL", test_url_validation),
        ("Извлечение данных", test_data_extraction),
        ("Генерация дашборда", test_dashboard_generation),
        ("Конфигурация", test_configuration),
        ("Сохранение результатов", test_save_results)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"ТЕСТ: {test_name}")
        print(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append((test_name, False))
    
    # Сводка результатов
    print(f"\n{'='*50}")
    print("СВОДКА РЕЗУЛЬТАТОВ ТЕСТИРОВАНИЯ")
    print(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\n📊 РЕЗУЛЬТАТ: {passed}/{total} тестов пройдено")
    print(f"📈 УСПЕШНОСТЬ: {(passed/total*100):.1f}%")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    elif passed >= total * 0.8:
        print("✅ БОЛЬШИНСТВО ТЕСТОВ ПРОЙДЕНО")
    else:
        print("⚠️ МНОГО ТЕСТОВ ПРОВАЛЕНО")
    
    return passed == total

def main():
    """Основная функция"""
    print("🧪 ТЕСТИРОВАНИЕ ИНТЕГРИРОВАННОГО ПАРСЕРА OZON")
    print("=" * 60)
    
    while True:
        print("\nВыберите действие:")
        print("1. Запустить все тесты")
        print("2. Тест инициализации парсера")
        print("3. Тест настройки драйвера")
        print("4. Тест валидации URL")
        print("5. Тест извлечения данных")
        print("6. Тест генерации дашборда")
        print("7. Тест конфигурации")
        print("8. Тест сохранения результатов")
        print("0. Выход")
        
        choice = input("\nВведите номер (0-8): ").strip()
        
        if choice == "0":
            print("👋 До свидания!")
            break
        elif choice == "1":
            run_all_tests()
        elif choice == "2":
            test_parser_initialization()
        elif choice == "3":
            test_driver_setup()
        elif choice == "4":
            test_url_validation()
        elif choice == "5":
            test_data_extraction()
        elif choice == "6":
            test_dashboard_generation()
        elif choice == "7":
            test_configuration()
        elif choice == "8":
            test_save_results()
        else:
            print("❌ Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main()
