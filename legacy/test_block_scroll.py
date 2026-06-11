#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест прокрутки блока с предприятиями
"""

import sys
import os

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from final_working_parser import FinalWorkingParser
from config import TARGET_BUSINESSES_COUNT

def test_block_scroll():
    """Тест прокрутки блока"""
    print("🧪 ТЕСТ ПРОКРУТКИ БЛОКА С ПРЕДПРИЯТИЯМИ")
    print("=" * 50)
    
    # URL для тестирования
    test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/?ll=39.806284%2C47.275656&z=12"
    
    print(f"\n🎯 ТЕСТ: Парсинг с прокруткой блока")
    print("-" * 30)
    
    # Создаем парсер
    parser = FinalWorkingParser(target_count=15)  # Тестируем на 15 предприятиях
    
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

def test_container_detection():
    """Тест обнаружения контейнера"""
    print("🧪 ТЕСТ ОБНАРУЖЕНИЯ КОНТЕЙНЕРА")
    print("=" * 40)
    
    test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/?ll=39.806284%2C47.275656&z=12"
    
    parser = FinalWorkingParser(target_count=1)
    
    try:
        if parser.setup_driver():
            if parser.navigate_to_search(test_url):
                print("🔍 Поиск контейнера с результатами...")
                container = parser.find_results_container()
                
                if container:
                    print("✅ Контейнер найден!")
                    print(f"   📊 Класс: {container.get_attribute('class')}")
                    
                    # Подсчитываем ссылки в контейнере
                    org_links = container.find_elements(By.XPATH, ".//a[contains(@href, '/org/')]")
                    print(f"   🔗 Ссылок на предприятия: {len(org_links)}")
                    
                    # Тестируем прокрутку контейнера
                    print("📜 Тестируем прокрутку контейнера...")
                    initial_count = parser.count_business_elements()
                    parser.scroll_results_container(container)
                    time.sleep(2)
                    final_count = parser.count_business_elements()
                    
                    print(f"   📈 Элементов до прокрутки: {initial_count}")
                    print(f"   📈 Элементов после прокрутки: {final_count}")
                else:
                    print("❌ Контейнер не найден")
                    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        parser.close()

if __name__ == "__main__":
    print("Выберите тест:")
    print("1. Полный тест парсинга с прокруткой блока")
    print("2. Тест обнаружения контейнера")
    
    choice = input("Введите номер (1 или 2): ").strip()
    
    if choice == "2":
        test_container_detection()
    else:
        test_block_scroll()
