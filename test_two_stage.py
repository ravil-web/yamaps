#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест двухэтапного парсера с кликами по карточкам
"""

import sys
import os
import time

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from src.browser_manager import BrowserManager
from src.business_card_extractor import BusinessCardExtractor
from src.data_saver import DataSaver

def test_two_stage():
    """Тест двухэтапного извлечения"""
    print("🔄 Тест двухэтапного парсера с кликами")
    print("=" * 60)
    
    # Настройка
    config = Config()
    config.HEADLESS = False  # Показать браузер для отладки
    config.DELAY_BETWEEN_REQUESTS = 2  # Задержка между кликами
    
    # Компоненты
    browser_manager = BrowserManager(config)
    extractor = BusinessCardExtractor(config)
    data_saver = DataSaver(config.OUTPUT_DIR)
    
    try:
        # 1. Инициализация браузера
        print("🚀 Инициализация браузера...")
        if not browser_manager.setup_driver():
            print("❌ Не удалось инициализировать браузер")
            return
        print("✅ Браузер инициализирован")
        
        # 2. Переход на страницу поиска
        test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/"
        print(f"📖 Переход на: {test_url}")
        
        if not browser_manager.navigate_to_url(test_url):
            print("❌ Не удалось перейти на страницу")
            return
        print("✅ Переход выполнен")
        
        # 3. Ожидание загрузки и прокрутка
        print("⏳ Ожидание загрузки...")
        time.sleep(5)
        
        print("📜 Прокрутка страницы...")
        browser_manager.scroll_page(max_scrolls=2)
        time.sleep(2)
        
        # 4. Двухэтапное извлечение данных
        print("🔄 Начинаем двухэтапное извлечение...")
        businesses = extractor.extract_businesses_two_stage(browser_manager.driver)
        
        # 5. Результаты
        print(f"📊 Результат: найдено {len(businesses)} предприятий")
        
        if businesses:
            print("\n📋 Первые 3 предприятия:")
            for i, business in enumerate(businesses[:3], 1):
                print(f"\n{i}. {business.get('name', 'Без названия')}")
                print(f"   📍 Адрес: {business.get('address', 'Не указан')}")
                print(f"   📞 Телефон: {business.get('phone', 'Не указан')}")
                print(f"   ⭐ Рейтинг: {business.get('rating', 'Не указан')}")
                print(f"   📝 Категории: {', '.join(business.get('categories', []))}")
                print(f"   🌐 Сайт: {business.get('website', 'Не указан')}")
                print(f"   🔧 Услуги: {business.get('services', 'Не указано')}")
                print(f"   📱 Соцсети: {len(business.get('social_links', []))} ссылок")
                print(f"   📊 Источник: {business.get('source', 'unknown')}")
            
            # 6. Сохранение данных
            print("\n💾 Сохранение данных...")
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"two_stage_test_{timestamp}.xlsx"
            filepath = data_saver.save_to_excel(businesses, filename)
            
            if filepath:
                print(f"✅ Данные сохранены: {filepath}")
                print(f"📈 Статистика:")
                print(f"   - Всего предприятий: {len(businesses)}")
                print(f"   - С телефонами: {len([b for b in businesses if b.get('phone')])}")
                print(f"   - С сайтами: {len([b for b in businesses if b.get('website')])}")
                print(f"   - С рейтингами: {len([b for b in businesses if b.get('rating')])}")
                print(f"   - Детальные данные: {len([b for b in businesses if b.get('source') == 'detailed'])}")
            else:
                print("❌ Ошибка сохранения")
        else:
            print("❌ Предприятия не найдены")
            print("💡 Возможные причины:")
            print("   - Изменилась структура Яндекс Карт")
            print("   - Селекторы устарели")
            print("   - Блокировка или капча")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n👀 Браузер оставлен открытым для анализа")
        print("Нажмите Enter для закрытия...")
        input()
        
        print("🔚 Закрытие браузера...")
        browser_manager.close()
        print("✅ Тест завершен")

if __name__ == "__main__":
    test_two_stage()
