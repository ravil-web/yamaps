#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест оптимизированной прокрутки
"""

import sys
import os

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from final_working_parser import FinalWorkingParser
from config import TARGET_BUSINESSES_COUNT

def test_optimized_scroll():
    """Тест оптимизированной прокрутки"""
    print("🧪 ТЕСТ ОПТИМИЗИРОВАННОЙ ПРОКРУТКИ")
    print("=" * 50)
    
    # URL для тестирования
    test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/?ll=39.806284%2C47.275656&z=12"
    
    print(f"\n🎯 ТЕСТ: Парсинг с оптимизированной прокруткой")
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

def test_scroll_performance():
    """Тест производительности прокрутки"""
    print("🧪 ТЕСТ ПРОИЗВОДИТЕЛЬНОСТИ ПРОКРУТКИ")
    print("=" * 40)
    
    test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/?ll=39.806284%2C47.275656&z=12"
    
    parser = FinalWorkingParser(target_count=1)
    
    try:
        if parser.setup_driver():
            if parser.navigate_to_search(test_url):
                print("🔍 Тестируем производительность прокрутки...")
                
                import time
                start_time = time.time()
                
                # Тестируем поиск контейнера
                container = parser.find_results_container()
                
                if container:
                    print("✅ Контейнер найден!")
                    
                    # Тестируем прокрутку
                    initial_count = parser.count_business_elements()
                    print(f"   📈 Начальное количество элементов: {initial_count}")
                    
                    # Тест прокрутки
                    parser.scroll_results_container(container)
                    time.sleep(1.5)
                    
                    # Тест кнопок
                    buttons_found = parser.click_load_more_buttons()
                    print(f"   📈 Кнопки найдены: {buttons_found}")
                    
                    final_count = parser.count_business_elements()
                    print(f"   📈 Финальное количество: {final_count}")
                    
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    print(f"\n⏱️ ВРЕМЯ ВЫПОЛНЕНИЯ: {duration:.2f} секунд")
                    print(f"📊 РЕЗУЛЬТАТ: +{final_count - initial_count} элементов")
                    
                    if duration < 10:
                        print("✅ ОТЛИЧНАЯ ПРОИЗВОДИТЕЛЬНОСТЬ!")
                    elif duration < 20:
                        print("✅ ХОРОШАЯ ПРОИЗВОДИТЕЛЬНОСТЬ!")
                    else:
                        print("⚠️ МЕДЛЕННАЯ ПРОИЗВОДИТЕЛЬНОСТЬ")
                else:
                    print("❌ Контейнер не найден")
                    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        parser.close()

if __name__ == "__main__":
    print("Выберите тест:")
    print("1. Полный тест парсинга с оптимизированной прокруткой")
    print("2. Тест производительности прокрутки")
    
    choice = input("Введите номер (1 или 2): ").strip()
    
    if choice == "2":
        test_scroll_performance()
    else:
        test_optimized_scroll()
