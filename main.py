#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Основной файл для запуска парсера Яндекс Карт
"""

import sys
import os

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import *
from src.parsers.yandex_parser import MainParser

def main():
    """Основная функция запуска парсера"""
    print("🚀 Запуск парсера Яндекс Карт")
    print(f"🎯 Цель: {TARGET_BUSINESSES_COUNT} предприятий")
    print(f"📄 URL: {SEARCH_URL}")
    print("-" * 50)
    
    # Запрос имени парсинга
    session_name = input("📝 Введите имя для этого парсинга (например, 'Стоматология_Ростов_2025'): ").strip()
    
    if not session_name:
        from datetime import datetime
        session_name = f"parsing_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"💡 Используется автоматическое имя: {session_name}")
    
    # Создание парсера с именем сессии
    parser = MainParser(session_name=session_name)
    
    try:
        # Парсинг предприятий
        print("🔍 Извлечение URL предприятий...")
        business_urls = parser.extract_business_urls()
        
        if not business_urls:
            print("❌ Не найдено ни одного предприятия!")
            return
        
        print(f"✅ Найдено {len(business_urls)} предприятий")
        
        # Парсинг данных предприятий
        print("📊 Парсинг данных предприятий...")
        results = parser.parse_businesses(business_urls)
        
        print(f"🎉 Парсинг завершен! Обработано: {len(results)} предприятий")
        
    except KeyboardInterrupt:
        print("\n⏹️ Парсинг прерван пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        parser.close()

if __name__ == "__main__":
    main()