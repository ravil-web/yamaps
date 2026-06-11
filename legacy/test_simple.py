#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Простой тест парсера с выводом ошибок
"""

import sys
import os
import traceback

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from src.main_parser import YandexMapsParser

def test_simple():
    """Простой тест парсера с детальным выводом"""
    print("🔧 Простой тест парсера с открытым браузером")
    print("=" * 50)
    
    try:
        # Создание конфигурации
        config = Config()
        config.HEADLESS = False  # Показать браузер
        config.DELAY_BETWEEN_REQUESTS = 5  # Больше задержка
        config.CAPTCHA_TIMEOUT = 120  # Больше времени на капчу
        
        # Создание парсера
        parser = YandexMapsParser(config)
        print("✅ Парсер создан")
        
        # Тест URL
        test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/"
        print(f"🔗 Тестовый URL: {test_url}")
        
        # Парсинг
        print("🚀 Запуск парсинга...")
        result = parser.parse_url(test_url, max_pages=1, save_format='excel')
        
        print("📊 Результат:")
        print(result)
        
        if result['success']:
            print("🎉 Парсинг успешен!")
        else:
            print(f"❌ Ошибка: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_simple()
