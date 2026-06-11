#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест новой улучшенной прокрутки
"""

import sys
import os

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from final_working_parser import FinalWorkingParser
from config import TARGET_BUSINESSES_COUNT

def test_new_scroll():
    """Тест новой прокрутки"""
    print("🧪 ТЕСТ НОВОЙ УЛУЧШЕННОЙ ПРОКРУТКИ")
    print("=" * 50)
    print(f"📋 Конфигурация: TARGET_BUSINESSES_COUNT = {TARGET_BUSINESSES_COUNT}")
    print("=" * 50)
    
    # URL для тестирования
    test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/?ll=39.806284%2C47.275656&z=12"
    
    print(f"\n🎯 ТЕСТ: Парсинг с улучшенной прокруткой")
    print("-" * 30)
    
    # Создаем парсер с небольшим количеством для теста
    parser = FinalWorkingParser(target_count=10)  # Тестируем на 10 предприятиях
    
    try:
        print("🚀 Запуск парсера...")
        success = parser.parse(test_url)
        
        if success:
            actual_count = len(parser.businesses)
            target_count = parser.target_count
            
            print(f"\n📊 РЕЗУЛЬТАТЫ:")
            print(f"✅ Успешно обработано: {actual_count} предприятий")
            print(f"🎯 Запрошено: {target_count}")
            
            if actual_count >= target_count:
                print(f"🎉 ЦЕЛЬ ДОСТИГНУТА!")
            else:
                print(f"⚠️ Цель не достигнута. Найдено только {actual_count} из {target_count}")
                
            # Показываем названия найденных предприятий
            if parser.businesses:
                print(f"\n📋 НАЙДЕННЫЕ ПРЕДПРИЯТИЯ:")
                for i, business in enumerate(parser.businesses[:5], 1):
                    print(f"   {i}. {business.get('name', 'Без названия')}")
                if len(parser.businesses) > 5:
                    print(f"   ... и еще {len(parser.businesses) - 5} предприятий")
        else:
            print("❌ Парсинг завершился с ошибками")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        parser.close()
    
    print()

def test_scroll_only():
    """Тест только прокрутки без парсинга"""
    print("🧪 ТЕСТ ТОЛЬКО ПРОКРУТКИ")
    print("=" * 30)
    
    test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/?ll=39.806284%2C47.275656&z=12"
    
    parser = FinalWorkingParser(target_count=1)  # Минимальный парсер
    
    try:
        if parser.setup_driver():
            if parser.navigate_to_search(test_url):
                print("📜 Тестируем только прокрутку...")
                parser.scroll_to_load_more()
                
                print("🔍 Тестируем подсчет элементов...")
                count = parser.count_business_elements()
                print(f"📊 Найдено элементов: {count}")
                
                print("🔍 Тестируем поиск ссылок...")
                links = parser.get_business_links()
                print(f"📊 Найдено ссылок: {len(links)}")
                
                if links:
                    print("📋 Первые 5 ссылок:")
                    for i, link in enumerate(links[:5], 1):
                        print(f"   {i}. {link}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        parser.close()

if __name__ == "__main__":
    print("Выберите тест:")
    print("1. Полный тест парсинга")
    print("2. Тест только прокрутки")
    
    choice = input("Введите номер (1 или 2): ").strip()
    
    if choice == "2":
        test_scroll_only()
    else:
        test_new_scroll()
