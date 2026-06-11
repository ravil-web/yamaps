#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест параллельного парсера Ozon
"""

import sys
import os

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ozon_parallel_parser import OzonParallelParser

def test_seller_products():
    """Тест парсинга товаров продавца"""
    print("🧪 ТЕСТ ПАРСИНГА ТОВАРОВ ПРОДАВЦА")
    print("=" * 50)
    
    # URL для тестирования (замените на реальный URL продавца)
    test_url = "https://www.ozon.ru/seller/example-seller-123456/"
    
    print(f"\n🎯 ТЕСТ: Парсинг товаров продавца")
    print("-" * 30)
    
    # Создаем парсер
    parser = OzonParallelParser(headless=False)
    
    try:
        print("🚀 Запуск парсера...")
        products = parser.parse_seller_products(test_url, max_products=20, max_pages=3)
        
        if products:
            print(f"\n📊 РЕЗУЛЬТАТЫ:")
            print(f"✅ Успешно найдено: {len(products)} товаров")
            
            # Показываем структуру данных
            if products:
                print(f"\n📋 СТРУКТУРА ДАННЫХ:")
                sample_product = products[0]
                for key, value in sample_product.items():
                    print(f"   {key}: {str(value)[:100]}...")
            
            # Показываем примеры найденных товаров
            print(f"\n📋 ПРИМЕРЫ НАЙДЕННЫХ ТОВАРОВ:")
            for i, product in enumerate(products[:10], 1):
                name = product.get('name', 'Без названия')
                price = product.get('price', 'Цена не указана')
                rating = product.get('rating', 'Рейтинг не указан')
                print(f"   {i}. {name[:60]}...")
                print(f"      💰 Цена: {price}")
                print(f"      ⭐ Рейтинг: {rating}")
                print()
            
            if len(products) > 10:
                print(f"   ... и еще {len(products) - 10} товаров")
            
            # Сохраняем результаты
            success = parser.save_results(products, "test_seller_products")
            if success:
                print("✅ Результаты сохранены")
            else:
                print("❌ Ошибка сохранения результатов")
        else:
            print("❌ Товары не найдены")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        parser.close()
    
    print()

def test_detailed_products():
    """Тест парсинга с детальной информацией"""
    print("🧪 ТЕСТ ПАРСИНГА С ДЕТАЛЬНОЙ ИНФОРМАЦИЕЙ")
    print("=" * 50)
    
    # URL для тестирования (замените на реальный URL продавца)
    test_url = "https://www.ozon.ru/seller/example-seller-123456/"
    
    print(f"\n🎯 ТЕСТ: Парсинг с детальной информацией")
    print("-" * 30)
    
    # Создаем парсер
    parser = OzonParallelParser(headless=False)
    
    try:
        print("🚀 Запуск парсера...")
        detailed_products = parser.parse_products_with_details(test_url, max_products=5, max_pages=1)
        
        if detailed_products:
            print(f"\n📊 РЕЗУЛЬТАТЫ:")
            print(f"✅ Успешно найдено: {len(detailed_products)} товаров с детальной информацией")
            
            # Показываем структуру данных
            if detailed_products:
                print(f"\n📋 СТРУКТУРА ДЕТАЛЬНЫХ ДАННЫХ:")
                sample_product = detailed_products[0]
                for key, value in sample_product.items():
                    print(f"   {key}: {str(value)[:100]}...")
            
            # Показываем примеры найденных товаров
            print(f"\n📋 ПРИМЕРЫ ДЕТАЛЬНОЙ ИНФОРМАЦИИ:")
            for i, product in enumerate(detailed_products[:3], 1):
                name = product.get('name', 'Без названия')
                price = product.get('price', 'Цена не указана')
                description = product.get('description', 'Описание отсутствует')
                specifications = product.get('specifications', 'Характеристики отсутствуют')
                seller = product.get('seller', 'Продавец не указан')
                sku = product.get('sku', 'SKU не найден')
                
                print(f"   {i}. {name[:60]}...")
                print(f"      💰 Цена: {price}")
                print(f"      📝 Описание: {description[:100]}...")
                print(f"      🔧 Характеристики: {specifications[:100]}...")
                print(f"      🏪 Продавец: {seller}")
                print(f"      🏷️ SKU: {sku}")
                print()
            
            # Сохраняем результаты
            success = parser.save_results(detailed_products, "test_detailed_products")
            if success:
                print("✅ Результаты сохранены")
            else:
                print("❌ Ошибка сохранения результатов")
        else:
            print("❌ Детальная информация не найдена")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        parser.close()
    
    print()

def test_data_structure_comparison():
    """Тест сравнения структуры данных с оригиналом"""
    print("🧪 ТЕСТ СРАВНЕНИЯ СТРУКТУРЫ ДАННЫХ")
    print("=" * 50)
    
    print(f"\n🎯 ТЕСТ: Сравнение с оригинальными данными")
    print("-" * 30)
    
    # Загружаем оригинальные данные для сравнения
    try:
        import json
        
        # Загружаем оригинальные данные
        with open('ozon_simple/seller_products.json', 'r', encoding='utf-8') as f:
            original_products = json.load(f)
        
        with open('ozon_simple/seller_detailed_products.json', 'r', encoding='utf-8') as f:
            original_detailed = json.load(f)
        
        print(f"📊 ОРИГИНАЛЬНЫЕ ДАННЫЕ:")
        print(f"   Товары продавца: {len(original_products)}")
        print(f"   Детальные товары: {len(original_detailed)}")
        
        # Анализируем структуру оригинальных данных
        if original_products:
            print(f"\n📋 СТРУКТУРА ОРИГИНАЛЬНЫХ ТОВАРОВ:")
            sample = original_products[0]
            for key, value in sample.items():
                print(f"   {key}: {type(value).__name__}")
        
        if original_detailed:
            print(f"\n📋 СТРУКТУРА ОРИГИНАЛЬНЫХ ДЕТАЛЬНЫХ ТОВАРОВ:")
            sample = original_detailed[0]
            for key, value in sample.items():
                print(f"   {key}: {type(value).__name__}")
        
        # Проверяем соответствие полей
        expected_fields_products = ['name', 'price', 'rating', 'reviews', 'link', 'delivery']
        expected_fields_detailed = ['name', 'price', 'rating', 'reviews', 'description', 'specifications', 'delivery', 'seller', 'sku', 'url']
        
        print(f"\n✅ ОЖИДАЕМЫЕ ПОЛЯ ДЛЯ ТОВАРОВ: {expected_fields_products}")
        print(f"✅ ОЖИДАЕМЫЕ ПОЛЯ ДЛЯ ДЕТАЛЬНЫХ ТОВАРОВ: {expected_fields_detailed}")
        
        # Проверяем наличие полей в оригинальных данных
        if original_products:
            actual_fields = list(original_products[0].keys())
            missing_fields = set(expected_fields_products) - set(actual_fields)
            extra_fields = set(actual_fields) - set(expected_fields_products)
            
            print(f"\n📊 АНАЛИЗ ПОЛЕЙ ТОВАРОВ:")
            print(f"   Найденные поля: {actual_fields}")
            if missing_fields:
                print(f"   ⚠️ Отсутствующие поля: {missing_fields}")
            if extra_fields:
                print(f"   ➕ Дополнительные поля: {extra_fields}")
        
        if original_detailed:
            actual_fields = list(original_detailed[0].keys())
            missing_fields = set(expected_fields_detailed) - set(actual_fields)
            extra_fields = set(actual_fields) - set(expected_fields_detailed)
            
            print(f"\n📊 АНАЛИЗ ПОЛЕЙ ДЕТАЛЬНЫХ ТОВАРОВ:")
            print(f"   Найденные поля: {actual_fields}")
            if missing_fields:
                print(f"   ⚠️ Отсутствующие поля: {missing_fields}")
            if extra_fields:
                print(f"   ➕ Дополнительные поля: {extra_fields}")
        
    except FileNotFoundError:
        print("❌ Оригинальные файлы данных не найдены")
    except Exception as e:
        print(f"❌ Ошибка анализа данных: {e}")
    
    print()

def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ ПАРАЛЛЕЛЬНОГО ПАРСЕРА OZON")
    print("=" * 60)
    
    while True:
        print("\nВыберите тест:")
        print("1. Тест парсинга товаров продавца")
        print("2. Тест парсинга с детальной информацией")
        print("3. Тест сравнения структуры данных")
        print("4. Запустить все тесты")
        print("0. Выход")
        
        choice = input("\nВведите номер теста (0-4): ").strip()
        
        if choice == "0":
            print("👋 До свидания!")
            break
        elif choice == "1":
            test_seller_products()
        elif choice == "2":
            test_detailed_products()
        elif choice == "3":
            test_data_structure_comparison()
        elif choice == "4":
            print("🔄 Запуск всех тестов...")
            test_data_structure_comparison()
            # test_seller_products()  # Закомментировано для быстрого тестирования
            # test_detailed_products()  # Закомментировано для быстрого тестирования
            print("✅ Все тесты завершены!")
        else:
            print("❌ Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    main()
