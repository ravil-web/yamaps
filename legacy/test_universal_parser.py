#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест универсального парсера
"""

import sys
import os

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from universal_parser import UniversalParser
from config_universal import TARGET_COUNT, EXAMPLE_URLS

def test_yandex_maps():
    """Тест парсинга Яндекс.Карт"""
    print("🧪 ТЕСТ ПАРСИНГА ЯНДЕКС.КАРТ")
    print("=" * 50)
    
    # URL для тестирования
    test_url = EXAMPLE_URLS['yandex_maps'][0]
    
    print(f"\n🎯 ТЕСТ: Парсинг Яндекс.Карт")
    print("-" * 30)
    
    # Создаем парсер
    parser = UniversalParser(headless=False, target_count=5)  # Тестируем на 5 предприятиях
    
    try:
        print("🚀 Запуск парсера...")
        success = parser.parse(test_url)
        
        if success:
            actual_count = len(parser.results)
            target_count = parser.target_count
            
            print(f"\n📊 РЕЗУЛЬТАТЫ:")
            print(f"✅ Успешно обработано: {actual_count} предприятий")
            print(f"🎯 Запрошено: {target_count}")
            
            if actual_count >= target_count:
                print(f"🎉 ЦЕЛЬ ДОСТИГНУТА!")
            else:
                print(f"⚠️ Цель не достигнута. Найдено только {actual_count} из {target_count}")
                
            # Показываем названия найденных предприятий
            if parser.results:
                print(f"\n📋 НАЙДЕННЫЕ ПРЕДПРИЯТИЯ:")
                for i, business in enumerate(parser.results[:10], 1):
                    print(f"   {i}. {business.get('name', 'Без названия')}")
                if len(parser.results) > 10:
                    print(f"   ... и еще {len(parser.results) - 10} предприятий")
        else:
            print("❌ Парсинг завершился с ошибками")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        parser.close()
    
    print()

def test_ozon():
    """Тест парсинга Ozon"""
    print("🧪 ТЕСТ ПАРСИНГА OZON")
    print("=" * 50)
    
    # URL для тестирования
    test_url = EXAMPLE_URLS['ozon'][0]
    
    print(f"\n🎯 ТЕСТ: Парсинг Ozon")
    print("-" * 30)
    
    # Создаем парсер
    parser = UniversalParser(headless=False, target_count=10)  # Тестируем на 10 товарах
    
    try:
        print("🚀 Запуск парсера...")
        success = parser.parse(test_url)
        
        if success:
            actual_count = len(parser.results)
            target_count = parser.target_count
            
            print(f"\n📊 РЕЗУЛЬТАТЫ:")
            print(f"✅ Успешно обработано: {actual_count} товаров")
            print(f"🎯 Запрошено: {target_count}")
            
            if actual_count >= target_count:
                print(f"🎉 ЦЕЛЬ ДОСТИГНУТА!")
            else:
                print(f"⚠️ Цель не достигнута. Найдено только {actual_count} из {target_count}")
                
            # Показываем названия найденных товаров
            if parser.results:
                print(f"\n📋 НАЙДЕННЫЕ ТОВАРЫ:")
                for i, product in enumerate(parser.results[:10], 1):
                    print(f"   {i}. {product.get('name', 'Без названия')}")
                if len(parser.results) > 10:
                    print(f"   ... и еще {len(parser.results) - 10} товаров")
        else:
            print("❌ Парсинг завершился с ошибками")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        parser.close()
    
    print()

def test_platform_detection():
    """Тест определения платформы"""
    print("🧪 ТЕСТ ОПРЕДЕЛЕНИЯ ПЛАТФОРМЫ")
    print("=" * 50)
    
    parser = UniversalParser()
    
    test_urls = [
        ("https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/", "yandex_maps"),
        ("https://www.ozon.ru/seller/example-seller-123456/", "ozon"),
        ("https://www.google.com/search?q=test", "unknown"),
        ("https://example.com", "unknown")
    ]
    
    print(f"\n🎯 ТЕСТ: Определение платформы по URL")
    print("-" * 30)
    
    for url, expected_platform in test_urls:
        detected_platform = parser.detect_platform(url)
        status = "✅" if detected_platform == expected_platform else "❌"
        print(f"{status} {url[:50]}... -> {detected_platform} (ожидалось: {expected_platform})")
    
    print()

def test_configuration():
    """Тест конфигурации"""
    print("🧪 ТЕСТ КОНФИГУРАЦИИ")
    print("=" * 50)
    
    print(f"\n🎯 ТЕСТ: Загрузка конфигурации")
    print("-" * 30)
    
    try:
        from config_universal import (
            TARGET_COUNT, SUPPORTED_PLATFORMS, HEADLESS_MODE,
            YANDEX_MAPS, OZON, EXAMPLE_URLS
        )
        
        print(f"✅ TARGET_COUNT: {TARGET_COUNT}")
        print(f"✅ SUPPORTED_PLATFORMS: {SUPPORTED_PLATFORMS}")
        print(f"✅ HEADLESS_MODE: {HEADLESS_MODE}")
        print(f"✅ YANDEX_MAPS enabled: {YANDEX_MAPS['enabled']}")
        print(f"✅ OZON enabled: {OZON['enabled']}")
        print(f"✅ EXAMPLE_URLS loaded: {len(EXAMPLE_URLS)} platforms")
        
        print(f"\n📋 Примеры URL:")
        for platform, urls in EXAMPLE_URLS.items():
            print(f"   {platform}: {len(urls)} URLs")
        
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
    
    print()

def test_save_results():
    """Тест сохранения результатов"""
    print("🧪 ТЕСТ СОХРАНЕНИЯ РЕЗУЛЬТАТОВ")
    print("=" * 50)
    
    print(f"\n🎯 ТЕСТ: Сохранение результатов")
    print("-" * 30)
    
    parser = UniversalParser()
    
    # Создаем тестовые данные
    test_data = [
        {
            'name': 'Тестовое предприятие 1',
            'address': 'Тестовый адрес 1',
            'phone': '+7 (999) 123-45-67',
            'rating': '4.5',
            'url': 'https://example.com/1'
        },
        {
            'name': 'Тестовое предприятие 2',
            'address': 'Тестовый адрес 2',
            'phone': '+7 (999) 123-45-68',
            'rating': '4.8',
            'url': 'https://example.com/2'
        }
    ]
    
    parser.results = test_data
    
    try:
        success = parser.save_results()
        if success:
            print("✅ Результаты успешно сохранены")
        else:
            print("❌ Ошибка сохранения результатов")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    print()

def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ УНИВЕРСАЛЬНОГО ПАРСЕРА")
    print("=" * 60)
    
    while True:
        print("\nВыберите тест:")
        print("1. Тест определения платформы")
        print("2. Тест конфигурации")
        print("3. Тест сохранения результатов")
        print("4. Тест парсинга Яндекс.Карт")
        print("5. Тест парсинга Ozon")
        print("6. Запустить все тесты")
        print("0. Выход")
        
        choice = input("\nВведите номер теста (0-6): ").strip()
        
        if choice == "0":
            print("👋 До свидания!")
            break
        elif choice == "1":
            test_platform_detection()
        elif choice == "2":
            test_configuration()
        elif choice == "3":
            test_save_results()
        elif choice == "4":
            test_yandex_maps()
        elif choice == "5":
            test_ozon()
        elif choice == "6":
            print("🔄 Запуск всех тестов...")
            test_platform_detection()
            test_configuration()
            test_save_results()
            # test_yandex_maps()  # Закомментировано для быстрого тестирования
            # test_ozon()  # Закомментировано для быстрого тестирования
            print("✅ Все тесты завершены!")
        else:
            print("❌ Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main()
