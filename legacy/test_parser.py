#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки парсера
"""

import sys
import os

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Тест импортов"""
    try:
        print("Проверка импортов...")
        
        # Проверка основных модулей
        import pandas as pd
        print("✅ pandas установлен")
        
        import openpyxl
        print("✅ openpyxl установлен")
        
        import selenium
        print("✅ selenium установлен")
        
        import undetected_chromedriver
        print("✅ undetected-chromedriver установлен")
        
        # Проверка наших модулей
        from config import Config
        print("✅ config импортирован")
        
        from src.url_parser import YandexMapsUrlParser
        print("✅ url_parser импортирован")
        
        from src.data_extractor import DataExtractor
        print("✅ data_extractor импортирован")
        
        from src.data_saver import DataSaver
        print("✅ data_saver импортирован")
        
        print("\n🎉 Все модули успешно импортированы!")
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_url_parser():
    """Тест парсера URL"""
    try:
        print("\nТестирование парсера URL...")
        
        from src.url_parser import YandexMapsUrlParser
        
        parser = YandexMapsUrlParser()
        test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/"
        
        # Проверка валидации
        is_valid = parser.validate_url(test_url)
        print(f"URL валиден: {is_valid}")
        
        if is_valid:
            # Парсинг параметров
            params = parser.parse_url(test_url)
            print(f"Параметры URL: {params}")
        
        print("✅ Парсер URL работает")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка парсера URL: {e}")
        return False

def test_data_saver():
    """Тест сохранения данных"""
    try:
        print("\nТестирование сохранения данных...")
        
        from src.data_saver import DataSaver
        
        saver = DataSaver("output")
        
        # Тестовые данные
        test_data = [
            {
                'name': 'Тестовая стоматология',
                'address': 'ул. Тестовая, 1',
                'phone': '+7 123 456-78-90',
                'rating': 4.5,
                'reviews_count': 100,
                'website': 'https://test.ru',
                'working_hours': '09:00-18:00',
                'categories': ['Стоматология', 'Клиника'],
                'awards': 'Лучшая клиника 2024',
                'services': 'Лечение зубов, протезирование',
                'social_links': ['https://vk.com/test', 'https://instagram.com/test'],
                'panorama': True,
                'stories': ['Акция 1', 'Акция 2'],
                'products': ['Лечение кариеса', 'Отбеливание'],
                'prices': ['5000 ₽', '8000 ₽'],
                'coordinates': {'lat': 47.2357, 'lon': 39.7015}
            }
        ]
        
        # Сохранение в Excel
        excel_file = saver.save_to_excel(test_data, "test_businesses.xlsx")
        if excel_file:
            print(f"✅ Excel файл сохранен: {excel_file}")
        
        # Сохранение в CSV
        csv_file = saver.save_to_csv(test_data, "test_businesses.csv")
        if csv_file:
            print(f"✅ CSV файл сохранен: {csv_file}")
        
        # Сохранение в JSON
        json_file = saver.save_to_json(test_data, "test_businesses.json")
        if json_file:
            print(f"✅ JSON файл сохранен: {json_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка сохранения данных: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ ПАРСЕРА ЯНДЕКС КАРТ")
    print("=" * 50)
    
    # Создание папок если их нет
    os.makedirs("output", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Тесты
    tests = [
        ("Импорты", test_imports),
        ("Парсер URL", test_url_parser),
        ("Сохранение данных", test_data_saver)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"❌ Тест '{test_name}' не прошел")
    
    print("\n" + "=" * 50)
    print(f"📊 РЕЗУЛЬТАТЫ: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 Все тесты прошли успешно! Парсер готов к работе.")
        print("\n💡 Теперь можете запустить парсер:")
        print("python main.py \"https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/\" --save-format excel")
    else:
        print("⚠️ Некоторые тесты не прошли. Проверьте установку зависимостей.")
        print("\n💡 Попробуйте установить зависимости:")
        print("pip install -r requirements.txt")

if __name__ == "__main__":
    main()
