#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тестовый скрипт для проверки логирования парсера
"""

import sys
import os
import logging

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_logging():
    """Тест системы логирования"""
    print("🧪 ТЕСТИРОВАНИЕ ЛОГИРОВАНИЯ")
    print("=" * 50)
    
    # Создание папок
    os.makedirs("logs", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    try:
        # Импорт модулей
        from config import Config
        from src.url_parser import YandexMapsUrlParser
        from src.data_saver import DataSaver
        
        print("✅ Модули импортированы")
        
        # Тест URL парсера
        print("\n🔍 Тест URL парсера...")
        parser = YandexMapsUrlParser()
        test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/"
        
        # Валидация
        is_valid = parser.validate_url(test_url)
        print(f"URL валиден: {is_valid}")
        
        if is_valid:
            # Парсинг
            params = parser.parse_url(test_url)
            print(f"Параметры: {params}")
        
        # Тест сохранения данных
        print("\n💾 Тест сохранения данных...")
        saver = DataSaver("output")
        
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
        excel_file = saver.save_to_excel(test_data, "test_logging.xlsx")
        if excel_file:
            print(f"✅ Excel файл создан: {excel_file}")
        
        # Сохранение в JSON
        json_file = saver.save_to_json(test_data, "test_logging.json")
        if json_file:
            print(f"✅ JSON файл создан: {json_file}")
        
        print("\n✅ Тестирование логирования завершено успешно!")
        print("📁 Проверьте папки 'logs' и 'output' для результатов")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_logging()
