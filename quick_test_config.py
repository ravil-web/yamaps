#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Быстрый тест конфигурации парсера
"""

import sys
import os

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import TARGET_BUSINESSES_COUNT
from final_working_parser import FinalWorkingParser

def test_config():
    """Тест конфигурации"""
    print("🔧 ТЕСТ КОНФИГУРАЦИИ ПАРСЕРА")
    print("=" * 40)
    
    print(f"📋 TARGET_BUSINESSES_COUNT = {TARGET_BUSINESSES_COUNT}")
    
    # Создаем парсер без параметров
    parser = FinalWorkingParser()
    
    print(f"🎯 Парсер создан с target_count = {parser.target_count}")
    
    if parser.target_count == TARGET_BUSINESSES_COUNT:
        print("✅ Конфигурация работает корректно!")
    else:
        print("❌ Ошибка в конфигурации!")
    
    print(f"📊 Тип значения: {type(parser.target_count)}")
    
    if parser.target_count == 0:
        print("🌐 Режим: ВСЕ НАЙДЕННЫЕ ПРЕДПРИЯТИЯ")
    else:
        print(f"🎯 Режим: КОНКРЕТНОЕ КОЛИЧЕСТВО ({parser.target_count})")

if __name__ == "__main__":
    test_config()
