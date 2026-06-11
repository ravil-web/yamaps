#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Быстрый тест с обновленными селекторами
"""

import sys
import os
import time

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from src.browser_manager import BrowserManager
from src.data_extractor import DataExtractor

def quick_test():
    """Быстрый тест извлечения данных"""
    print("⚡ Быстрый тест с обновленными селекторами")
    print("=" * 50)
    
    config = Config()
    config.HEADLESS = False
    
    browser_manager = BrowserManager(config)
    data_extractor = DataExtractor()
    
    try:
        print("🚀 Запуск браузера...")
        if not browser_manager.setup_driver():
            return
        
        test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/"
        print(f"📖 Переход: {test_url}")
        
        if not browser_manager.navigate_to_url(test_url):
            return
            
        print("⏳ Ожидание загрузки...")
        time.sleep(8)  # Больше времени на загрузку
        
        print("📜 Прокрутка...")
        browser_manager.scroll_page(max_scrolls=3)
        time.sleep(3)
        
        print("🔍 Извлечение данных...")
        businesses = data_extractor.extract_businesses(browser_manager.driver)
        
        print(f"📊 Результат: {len(businesses)} предприятий")
        
        if businesses:
            print("\n✅ Первое найденное предприятие:")
            business = businesses[0]
            for key, value in business.items():
                if value:  # Показать только заполненные поля
                    print(f"   {key}: {value}")
        else:
            print("❌ Предприятия не найдены")
            
            # Дополнительная диагностика
            print("\n🔧 Диагностика:")
            driver = browser_manager.driver
            
            # Проверим каждый селектор
            for i, selector in enumerate(data_extractor.selectors['business_cards']):
                try:
                    from selenium.webdriver.common.by import By
                    elements = driver.find_elements(By.XPATH, selector)
                    print(f"   Селектор {i+1}: {len(elements)} элементов")
                    if elements and len(elements) > 0:
                        # Попробуем получить текст первого элемента
                        try:
                            text = elements[0].text[:100]
                            print(f"      Текст: {text}...")
                        except:
                            print(f"      Текст: не удалось получить")
                except Exception as e:
                    print(f"   Селектор {i+1}: ошибка - {e}")
            
        print("\n👀 Браузер оставлен открытым. Нажмите Enter для закрытия...")
        input()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        browser_manager.close()

if __name__ == "__main__":
    quick_test()
