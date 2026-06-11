#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ручной тест парсера с открытым браузером и возможностью ручного решения капчи
"""

import sys
import os
import time

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from src.browser_manager import BrowserManager
from src.data_extractor import DataExtractor
from src.data_saver import DataSaver

def manual_test():
    """Ручной тест с пошаговым выполнением"""
    print("🔧 Ручной тест парсера с возможностью решения капчи")
    print("=" * 60)
    
    # Создание конфигурации
    config = Config()
    config.HEADLESS = False  # Показать браузер
    config.DELAY_BETWEEN_REQUESTS = 3
    
    # Создание менеджера браузера
    browser_manager = BrowserManager(config)
    data_extractor = DataExtractor()
    data_saver = DataSaver(config.OUTPUT_DIR)
    
    try:
        # 1. Инициализация браузера
        print("1️⃣ Инициализация браузера...")
        if not browser_manager.setup_driver():
            print("❌ Не удалось инициализировать браузер")
            return
        print("✅ Браузер инициализирован")
        
        # 2. Переход на страницу
        test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/"
        print(f"2️⃣ Переход на: {test_url}")
        
        if not browser_manager.navigate_to_url(test_url):
            print("❌ Не удалось перейти на страницу")
            return
        print("✅ Переход выполнен")
        
        # 3. Проверка капчи
        print("3️⃣ Проверка капчи...")
        if browser_manager.check_captcha():
            print("⚠️ КАПЧА ОБНАРУЖЕНА!")
            print("👋 Решите капчу в открытом браузере и нажмите Enter для продолжения...")
            input()  # Ждем нажатия Enter
            
            # Проверяем снова
            if browser_manager.check_captcha():
                print("❌ Капча все еще присутствует")
                return
            else:
                print("✅ Капча решена!")
        else:
            print("✅ Капча не обнаружена")
        
        # 4. Прокрутка страницы
        print("4️⃣ Прокрутка страницы для загрузки контента...")
        browser_manager.scroll_page(max_scrolls=3)
        print("✅ Прокрутка завершена")
        
        # 5. Извлечение данных
        print("5️⃣ Извлечение данных...")
        businesses = data_extractor.extract_businesses(browser_manager.driver)
        
        if businesses:
            print(f"✅ Найдено {len(businesses)} предприятий")
            
            # Показать первые 3 предприятия для примера
            print("\n📋 Первые найденные предприятия:")
            for i, business in enumerate(businesses[:3], 1):
                print(f"{i}. {business.get('name', 'Без названия')}")
                print(f"   📍 {business.get('address', 'Без адреса')}")
                print(f"   📞 {business.get('phone', 'Без телефона')}")
                print(f"   ⭐ {business.get('rating', 'Без рейтинга')}")
                print()
            
            # 6. Сохранение данных
            print("6️⃣ Сохранение данных...")
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"manual_test_{timestamp}.xlsx"
            filepath = data_saver.save_to_excel(businesses, filename)
            
            if filepath:
                print(f"✅ Данные сохранены: {filepath}")
            else:
                print("❌ Ошибка сохранения")
        else:
            print("⚠️ Предприятия не найдены")
            print("💡 Возможные причины:")
            print("   - Селекторы устарели")
            print("   - Страница не загрузилась полностью")
            print("   - Изменилась структура сайта")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("7️⃣ Закрытие браузера...")
        browser_manager.close()
        print("✅ Тест завершен")

if __name__ == "__main__":
    manual_test()
