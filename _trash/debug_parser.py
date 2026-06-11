#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Диагностический скрипт для проверки парсера
"""

import sys
import os
import traceback

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Тест импортов"""
    print("🔍 Тестирование импортов...")
    
    try:
        from config import Config
        print("✅ config импортирован")
    except Exception as e:
        print(f"❌ Ошибка импорта config: {e}")
        return False
    
    try:
        from src.url_parser import YandexMapsUrlParser
        print("✅ url_parser импортирован")
    except Exception as e:
        print(f"❌ Ошибка импорта url_parser: {e}")
        return False
    
    try:
        from src.browser_manager import BrowserManager
        print("✅ browser_manager импортирован")
    except Exception as e:
        print(f"❌ Ошибка импорта browser_manager: {e}")
        return False
    
    try:
        from src.data_extractor import DataExtractor
        print("✅ data_extractor импортирован")
    except Exception as e:
        print(f"❌ Ошибка импорта data_extractor: {e}")
        return False
    
    try:
        from src.data_saver import DataSaver
        print("✅ data_saver импортирован")
    except Exception as e:
        print(f"❌ Ошибка импорта data_saver: {e}")
        return False
    
    try:
        from src.main_parser import YandexMapsParser
        print("✅ main_parser импортирован")
    except Exception as e:
        print(f"❌ Ошибка импорта main_parser: {e}")
        return False
    
    return True

def test_url_parser():
    """Тест парсера URL"""
    print("\n🔍 Тестирование парсера URL...")
    
    try:
        from src.url_parser import YandexMapsUrlParser
        
        parser = YandexMapsUrlParser()
        test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/"
        
        # Валидация
        is_valid = parser.validate_url(test_url)
        print(f"URL валиден: {is_valid}")
        
        if is_valid:
            # Парсинг
            params = parser.parse_url(test_url)
            print(f"Параметры: {params}")
            return True
        else:
            print("❌ URL не прошел валидацию")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка парсера URL: {e}")
        traceback.print_exc()
        return False

def test_data_saver():
    """Тест сохранения данных"""
    print("\n💾 Тестирование сохранения данных...")
    
    try:
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
        excel_file = saver.save_to_excel(test_data, "debug_test.xlsx")
        if excel_file:
            print(f"✅ Excel файл создан: {excel_file}")
            return True
        else:
            print("❌ Ошибка создания Excel файла")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка сохранения данных: {e}")
        traceback.print_exc()
        return False

def test_main_parser():
    """Тест основного парсера"""
    print("\n🚀 Тестирование основного парсера...")
    
    try:
        from config import Config
        from src.main_parser import YandexMapsParser
        
        # Создание конфигурации
        config = Config()
        config.HEADLESS = False  # Показать браузер для отладки
        config.DELAY_BETWEEN_REQUESTS = 1
        
        # Создание парсера
        parser = YandexMapsParser(config)
        print("✅ Парсер создан")
        
        # Тест URL
        test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/"
        
        # Парсинг (только валидация URL, без запуска браузера)
        print("🔍 Тестирование валидации URL...")
        if parser.url_parser.validate_url(test_url):
            print("✅ URL валиден")
            params = parser.url_parser.parse_url(test_url)
            print(f"📊 Параметры: {params}")
            return True
        else:
            print("❌ URL невалиден")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка основного парсера: {e}")
        traceback.print_exc()
        return False

def main():
    """Основная функция диагностики"""
    print("🔧 ДИАГНОСТИКА ПАРСЕРА ЯНДЕКС КАРТ")
    print("=" * 50)
    
    # Создание папок
    os.makedirs("output", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Тесты
    tests = [
        ("Импорты", test_imports),
        ("Парсер URL", test_url_parser),
        ("Сохранение данных", test_data_saver),
        ("Основной парсер", test_main_parser)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} - ПРОЙДЕН")
        else:
            print(f"❌ {test_name} - НЕ ПРОЙДЕН")
    
    print("\n" + "=" * 50)
    print(f"📊 РЕЗУЛЬТАТЫ: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 Все тесты прошли! Парсер готов к работе.")
        print("\n💡 Теперь можете запустить парсер:")
        print("python main.py \"https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/\" --save-format excel")
    else:
        print("⚠️ Некоторые тесты не прошли. Проверьте ошибки выше.")
        print("\n💡 Возможные решения:")
        print("1. Установите зависимости: pip install -r requirements.txt")
        print("2. Проверьте версию Python (рекомендуется 3.8+)")
        print("3. Убедитесь, что Chrome установлен")

if __name__ == "__main__":
    main()
