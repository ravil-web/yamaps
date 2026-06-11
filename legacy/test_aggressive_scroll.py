#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест агрессивной прокрутки
"""

import sys
import os

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from final_working_parser import FinalWorkingParser
from config import TARGET_BUSINESSES_COUNT

def test_aggressive_scroll():
    """Тест агрессивной прокрутки"""
    print("🧪 ТЕСТ АГРЕССИВНОЙ ПРОКРУТКИ")
    print("=" * 50)
    
    # URL для тестирования
    test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/?ll=39.806284%2C47.275656&z=12"
    
    print(f"\n🎯 ТЕСТ: Парсинг с агрессивной прокруткой")
    print("-" * 30)
    
    # Создаем парсер
    parser = FinalWorkingParser(target_count=20)  # Тестируем на 20 предприятиях
    
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
                for i, business in enumerate(parser.businesses[:10], 1):
                    print(f"   {i}. {business.get('name', 'Без названия')}")
                if len(parser.businesses) > 10:
                    print(f"   ... и еще {len(parser.businesses) - 10} предприятий")
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
    """Тест только прокрутки"""
    print("🧪 ТЕСТ ТОЛЬКО ПРОКРУТКИ")
    print("=" * 40)
    
    test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/?ll=39.806284%2C47.275656&z=12"
    
    parser = FinalWorkingParser(target_count=1)
    
    try:
        if parser.setup_driver():
            if parser.navigate_to_search(test_url):
                print("🔍 Тестируем поиск контейнера...")
                container = parser.find_results_container()
                
                if container:
                    print("✅ Контейнер найден!")
                    print(f"   📊 Класс: {container.get_attribute('class')}")
                    
                    # Тестируем прокрутку
                    print("📜 Тестируем прокрутку...")
                    initial_count = parser.count_business_elements()
                    print(f"   📈 Начальное количество элементов: {initial_count}")
                    
                    # Тестируем обычную прокрутку
                    print("   🔄 Обычная прокрутка...")
                    parser.scroll_results_container(container)
                    time.sleep(2)
                    count_after_normal = parser.count_business_elements()
                    print(f"   📈 После обычной прокрутки: {count_after_normal}")
                    
                    # Тестируем агрессивную прокрутку
                    print("   🚀 Агрессивная прокрутка...")
                    parser.aggressive_scroll()
                    time.sleep(2)
                    count_after_aggressive = parser.count_business_elements()
                    print(f"   📈 После агрессивной прокрутки: {count_after_aggressive}")
                    
                    print(f"   📊 Результат: +{count_after_aggressive - initial_count} элементов")
                else:
                    print("❌ Контейнер не найден")
                    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        parser.close()

if __name__ == "__main__":
    print("Выберите тест:")
    print("1. Полный тест парсинга с агрессивной прокруткой")
    print("2. Тест только прокрутки")
    
    choice = input("Введите номер (1 или 2): ").strip()
    
    if choice == "2":
        test_scroll_only()
    else:
        test_aggressive_scroll()
