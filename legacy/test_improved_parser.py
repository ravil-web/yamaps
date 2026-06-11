#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест улучшенного парсера с исправлениями для парсинга большего количества предприятий
"""

import sys
import os

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from final_working_parser import FinalWorkingParser
from config import TARGET_BUSINESSES_COUNT

def test_improved_parser():
    """Тест улучшенного парсера"""
    print("🧪 ТЕСТ УЛУЧШЕННОГО ПАРСЕРА")
    print("=" * 50)
    print(f"📋 Конфигурация: TARGET_BUSINESSES_COUNT = {TARGET_BUSINESSES_COUNT}")
    print("=" * 50)
    
    # URL для тестирования
    test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/?ll=39.806284%2C47.275656&z=12"
    
    # Тестируем с конфигурационным значением
    print(f"\n🎯 ТЕСТ: Парсинг с конфигурационным значением")
    print("-" * 30)
    
    parser = FinalWorkingParser()  # Используем значение из конфигурации
    
    try:
        success = parser.parse(test_url)
        
        if success:
            actual_count = len(parser.businesses)
            target_count = parser.target_count
            
            print(f"✅ Успешно: {actual_count} предприятий")
            print(f"🎯 Запрошено: {target_count if target_count > 0 else 'ВСЕ НАЙДЕННЫЕ'}")
            
            if target_count > 0:
                if actual_count >= target_count:
                    print(f"🎉 ЦЕЛЬ ДОСТИГНУТА!")
                else:
                    print(f"⚠️ Цель не достигнута. Найдено только {actual_count} из {target_count}")
            else:
                print(f"🎉 ПАРСИНГ ВСЕХ НАЙДЕННЫХ ЗАВЕРШЕН!")
        else:
            print("❌ Парсинг завершился с ошибками")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        parser.close()
    
    print()

if __name__ == "__main__":
    test_improved_parser()