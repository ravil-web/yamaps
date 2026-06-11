#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Файл запуска параллельного парсера Ozon
"""

import sys
import os
import time
from datetime import datetime

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ozon_parallel_parser import OzonParallelParser

def print_banner():
    """Вывод баннера"""
    print("=" * 60)
    print("🛒 ПАРАЛЛЕЛЬНЫЙ ПАРСЕР OZON")
    print("=" * 60)
    print("Возможности:")
    print("  • Парсинг товаров продавцов")
    print("  • Парсинг с детальной информацией")
    print("  • Сохранение в JSON формате")
    print("  • Автоматическая прокрутка и пагинация")
    print("=" * 60)

def get_user_input():
    """Получение входных данных от пользователя"""
    print("\n📝 ВВОД ПАРАМЕТРОВ")
    print("-" * 30)
    
    # URL для парсинга
    print("\n🌐 Введите URL продавца Ozon:")
    print("Примеры:")
    print("  https://www.ozon.ru/seller/example-seller-123456/")
    print("  https://www.ozon.ru/category/knigi-16500/")
    print("  https://www.ozon.ru/search/?text=книги")
    
    url = input("\nURL: ").strip()
    if not url:
        print("❌ URL не может быть пустым!")
        return None
    
    # Тип парсинга
    print(f"\n📊 Тип парсинга:")
    print("  1. Товары продавца (быстрый)")
    print("  2. Детальная информация (медленный)")
    print("  3. Оба типа")
    
    try:
        parse_type = input("Выберите тип (1-3): ").strip()
        if parse_type not in ['1', '2', '3']:
            print("⚠️ Неверный выбор, используется тип 1")
            parse_type = '1'
    except:
        parse_type = '1'
    
    # Количество товаров
    print(f"\n📊 Количество товаров для парсинга:")
    print(f"  (по умолчанию: 20 для быстрого, 5 для детального)")
    
    try:
        count_input = input("Количество: ").strip()
        if count_input:
            target_count = int(count_input)
        else:
            target_count = 20 if parse_type == '1' else 5
    except ValueError:
        print("⚠️ Неверный формат, используется значение по умолчанию")
        target_count = 20 if parse_type == '1' else 5
    
    # Количество страниц
    print(f"\n📄 Количество страниц для парсинга:")
    print(f"  (по умолчанию: 3 для быстрого, 1 для детального)")
    
    try:
        pages_input = input("Количество страниц: ").strip()
        if pages_input:
            max_pages = int(pages_input)
        else:
            max_pages = 3 if parse_type == '1' else 1
    except ValueError:
        print("⚠️ Неверный формат, используется значение по умолчанию")
        max_pages = 3 if parse_type == '1' else 1
    
    # Режим работы
    print(f"\n🖥️ Режим работы браузера:")
    print(f"  (0 = с окном, 1 = без окна, по умолчанию: 0)")
    
    try:
        headless_input = input("Режим (0/1): ").strip()
        if headless_input:
            headless = bool(int(headless_input))
        else:
            headless = False
    except ValueError:
        print("⚠️ Неверный формат, используется значение по умолчанию")
        headless = False
    
    return {
        'url': url,
        'parse_type': parse_type,
        'target_count': target_count,
        'max_pages': max_pages,
        'headless': headless
    }

def validate_url(url):
    """Проверка URL"""
    if not url.startswith(('http://', 'https://')):
        print("❌ URL должен начинаться с http:// или https://")
        return False
    
    if 'ozon.ru' not in url:
        print("⚠️ URL не содержит ozon.ru. Парсинг может не работать корректно.")
        response = input("Продолжить? (y/n): ").strip().lower()
        if response not in ['y', 'yes', 'да', 'д']:
            return False
    
    return True

def print_parse_info(parse_type, target_count, max_pages):
    """Вывод информации о парсинге"""
    print(f"\n🔍 НАСТРОЙКИ ПАРСИНГА")
    print("-" * 30)
    
    if parse_type == '1':
        print("📋 Тип: Товары продавца (быстрый)")
        print("📊 Количество товаров: " + str(target_count))
        print("📄 Количество страниц: " + str(max_pages))
        print("⚡ Скорость: Быстрая")
    elif parse_type == '2':
        print("📋 Тип: Детальная информация (медленный)")
        print("📊 Количество товаров: " + str(target_count))
        print("📄 Количество страниц: " + str(max_pages))
        print("⚡ Скорость: Медленная")
    else:
        print("📋 Тип: Оба типа")
        print("📊 Количество товаров: " + str(target_count))
        print("📄 Количество страниц: " + str(max_pages))
        print("⚡ Скорость: Средняя")

def print_results_summary(products, detailed_products, parse_type):
    """Вывод сводки результатов"""
    print(f"\n📊 СВОДКА РЕЗУЛЬТАТОВ")
    print("=" * 30)
    
    if parse_type in ['1', '3']:
        products_count = len(products) if products else 0
        print(f"🛒 Товары продавца: {products_count}")
        
        if products:
            print(f"\n📋 ПРИМЕРЫ ТОВАРОВ:")
            for i, product in enumerate(products[:5], 1):
                name = product.get('name', 'Без названия')
                price = product.get('price', 'Цена не указана')
                print(f"   {i}. {name[:50]}... - {price}")
            
            if len(products) > 5:
                print(f"   ... и еще {len(products) - 5} товаров")
    
    if parse_type in ['2', '3']:
        detailed_count = len(detailed_products) if detailed_products else 0
        print(f"📝 Детальная информация: {detailed_count}")
        
        if detailed_products:
            print(f"\n📋 ПРИМЕРЫ ДЕТАЛЬНОЙ ИНФОРМАЦИИ:")
            for i, product in enumerate(detailed_products[:3], 1):
                name = product.get('name', 'Без названия')
                price = product.get('price', 'Цена не указана')
                description = product.get('description', 'Описание отсутствует')
                print(f"   {i}. {name[:40]}... - {price}")
                print(f"      📝 {description[:60]}...")
    
    total_count = (len(products) if products else 0) + (len(detailed_products) if detailed_products else 0)
    print(f"\n🎯 Всего обработано: {total_count} товаров")

def main():
    """Основная функция"""
    print_banner()
    
    # Получение параметров от пользователя
    params = get_user_input()
    if not params:
        return
    
    url = params['url']
    parse_type = params['parse_type']
    target_count = params['target_count']
    max_pages = params['max_pages']
    headless = params['headless']
    
    # Проверка URL
    if not validate_url(url):
        return
    
    print_parse_info(parse_type, target_count, max_pages)
    
    # Подтверждение запуска
    print(f"\n🚀 ГОТОВ К ЗАПУСКУ")
    print("-" * 20)
    print(f"URL: {url}")
    print(f"Тип парсинга: {parse_type}")
    print(f"Количество товаров: {target_count}")
    print(f"Количество страниц: {max_pages}")
    print(f"Режим: {'без окна' if headless else 'с окном'}")
    
    response = input("\nЗапустить парсинг? (y/n): ").strip().lower()
    if response not in ['y', 'yes', 'да', 'д']:
        print("❌ Парсинг отменен")
        return
    
    # Запуск парсинга
    print(f"\n🔄 ЗАПУСК ПАРСИНГА")
    print("=" * 30)
    start_time = time.time()
    
    parser = OzonParallelParser(headless=headless)
    products = []
    detailed_products = []
    
    try:
        # Парсинг товаров продавца
        if parse_type in ['1', '3']:
            print("\n🛒 ПАРСИНГ ТОВАРОВ ПРОДАВЦА")
            print("-" * 25)
            products = parser.parse_seller_products(url, max_products=target_count, max_pages=max_pages)
            
            if products:
                parser.save_results(products, "seller_products")
                print(f"✅ Товары продавца сохранены")
            else:
                print("❌ Товары продавца не найдены")
        
        # Парсинг с детальной информацией
        if parse_type in ['2', '3']:
            print("\n📝 ПАРСИНГ С ДЕТАЛЬНОЙ ИНФОРМАЦИЕЙ")
            print("-" * 25)
            detailed_products = parser.parse_products_with_details(url, max_products=target_count, max_pages=max_pages)
            
            if detailed_products:
                parser.save_results(detailed_products, "seller_detailed_products")
                print(f"✅ Детальная информация сохранена")
            else:
                print("❌ Детальная информация не найдена")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n✅ ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!")
        print(f"⏱️ Время выполнения: {duration:.1f} секунд")
        
        # Вывод сводки результатов
        print_results_summary(products, detailed_products, parse_type)
    
    except KeyboardInterrupt:
        print(f"\n⚠️ ПАРСИНГ ПРЕРВАН ПОЛЬЗОВАТЕЛЕМ")
        if products or detailed_products:
            print("💾 Сохранение частичных результатов...")
            if products:
                parser.save_results(products, "seller_products")
            if detailed_products:
                parser.save_results(detailed_products, "seller_detailed_products")
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
    finally:
        parser.close()
    
    print(f"\n👋 РАБОТА ЗАВЕРШЕНА")
    print("=" * 30)

if __name__ == "__main__":
    main()
