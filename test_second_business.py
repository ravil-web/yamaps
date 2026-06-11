#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест парсинга только второго предприятия для проверки скорости
"""

import time
from single_business_parser import SingleBusinessParser

def test_second_business():
    print("🔍 ТЕСТ ВТОРОГО ПРЕДПРИЯТИЯ")
    print("=" * 50)
    
    # URL второго предприятия (медленного)
    slow_url = "https://yandex.ru/maps/org/stomatologiya_kolomakinykh/63665148745/"
    
    parser = SingleBusinessParser()
    parser.max_products = 10  # Ограничиваем до 10 товаров для быстрого теста
    
    try:
        start_time = time.time()
        
        print(f"📄 URL: {slow_url}")
        print(f"🎯 Лимит товаров: {parser.max_products}")
        
        result = parser.parse_single_business(slow_url)
        
        total_time = time.time() - start_time
        
        if result:
            products_count = len(result.get('products_and_services', []))
            print(f"\n✅ РЕЗУЛЬТАТ:")
            print(f"   📊 Найдено товаров: {products_count}")
            print(f"   ⏱️ Общее время: {total_time:.1f}с")
            print(f"   ⚡ Время на товар: {total_time/products_count:.2f}с" if products_count > 0 else "   ⚡ Время на товар: н/д")
            
            # Показать первые несколько товаров
            products = result.get('products_and_services', [])
            print(f"\n🛍️ ПЕРВЫЕ ТОВАРЫ:")
            for i, product in enumerate(products[:5], 1):
                print(f"   {i}. {product.get('title', 'Без названия')} - {product.get('price', 'Без цены')}")
        else:
            print(f"\n❌ ОШИБКА: Данные не получены за {total_time:.1f}с")
            
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
    
    finally:
        parser.close()

if __name__ == "__main__":
    test_second_business()
