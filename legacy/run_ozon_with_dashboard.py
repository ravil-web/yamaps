#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Запуск парсера Ozon с созданием дашборда
"""

import sys
import os
import time
from datetime import datetime

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ozon_parser_integrated import OzonParserIntegrated
from ozon_dashboard_generator import OzonDashboardGenerator
from config import TARGET_BUSINESSES_COUNT

def print_banner():
    """Вывод баннера"""
    print("=" * 60)
    print("🛒 ПАРСЕР OZON С ДАШБОРДОМ")
    print("=" * 60)
    print("Возможности:")
    print("  • Парсинг товаров продавцов")
    print("  • Парсинг результатов поиска")
    print("  • Создание интерактивного дашборда")
    print("  • Сохранение в JSON и Excel")
    print("=" * 60)

def get_user_input():
    """Получение входных данных от пользователя"""
    print("\n📝 ВВОД ПАРАМЕТРОВ")
    print("-" * 30)
    
    # URL для парсинга
    print("\n🌐 Введите URL для парсинга:")
    print("Примеры:")
    print("  • Продавец: https://www.ozon.ru/seller/example-seller-123456/")
    print("  • Поиск: https://www.ozon.ru/search/?text=книги")
    print("  • Категория: https://www.ozon.ru/category/knigi-16500/")
    
    url = input("\nURL: ").strip()
    if not url:
        print("❌ URL не может быть пустым!")
        return None
    
    # Количество товаров
    print(f"\n📊 Количество товаров для парсинга:")
    print(f"  (0 = все найденные, по умолчанию: {TARGET_BUSINESSES_COUNT})")
    
    try:
        count_input = input("Количество: ").strip()
        if count_input:
            target_count = int(count_input)
        else:
            target_count = TARGET_BUSINESSES_COUNT
    except ValueError:
        print("⚠️ Неверный формат, используется значение по умолчанию")
        target_count = TARGET_BUSINESSES_COUNT
    
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
        'target_count': target_count,
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

def print_parse_info(url, target_count, headless):
    """Вывод информации о парсинге"""
    print(f"\n🔍 НАСТРОЙКИ ПАРСИНГА")
    print("-" * 30)
    
    # Определяем тип страницы
    if '/seller/' in url:
        page_type = "Продавец"
    elif '/search/' in url:
        page_type = "Поиск"
    elif '/category/' in url:
        page_type = "Категория"
    else:
        page_type = "Неизвестный"
    
    print(f"📋 Тип страницы: {page_type}")
    print(f"📊 Количество товаров: {target_count if target_count > 0 else 'все найденные'}")
    print(f"🖥️ Режим браузера: {'без окна' if headless else 'с окном'}")
    print(f"⚡ Скорость: {'быстрая' if headless else 'средняя'}")

def print_results_summary(products, target_count, success_rate):
    """Вывод сводки результатов"""
    print(f"\n📊 СВОДКА РЕЗУЛЬТАТОВ")
    print("=" * 30)
    
    actual_count = len(products)
    print(f"🎯 Запрошено: {target_count if target_count > 0 else 'все найденные'}")
    print(f"✅ Найдено: {actual_count}")
    
    if target_count > 0:
        print(f"📈 Успешность: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 ОТЛИЧНЫЙ РЕЗУЛЬТАТ!")
        elif success_rate >= 50:
            print("✅ ХОРОШИЙ РЕЗУЛЬТАТ")
        else:
            print("⚠️ Низкая успешность")
    else:
        print("📋 Парсинг всех найденных товаров завершен")
    
    # Показываем примеры найденных товаров
    if products:
        print(f"\n📋 ПРИМЕРЫ НАЙДЕННЫХ ТОВАРОВ:")
        for i, product in enumerate(products[:5], 1):
            name = product.get('name', 'Без названия')
            price = product.get('price', 'Цена не указана')
            print(f"   {i}. {name[:60]}...")
            print(f"      💰 Цена: {price}")
        
        if len(products) > 5:
            print(f"   ... и еще {len(products) - 5} товаров")

def main():
    """Основная функция"""
    print_banner()
    
    # Получение параметров от пользователя
    params = get_user_input()
    if not params:
        return
    
    url = params['url']
    target_count = params['target_count']
    headless = params['headless']
    
    # Проверка URL
    if not validate_url(url):
        return
    
    print_parse_info(url, target_count, headless)
    
    # Подтверждение запуска
    print(f"\n🚀 ГОТОВ К ЗАПУСКУ")
    print("-" * 20)
    print(f"URL: {url}")
    print(f"Количество товаров: {target_count if target_count > 0 else 'все найденные'}")
    print(f"Режим: {'без окна' if headless else 'с окном'}")
    
    response = input("\nЗапустить парсинг? (y/n): ").strip().lower()
    if response not in ['y', 'yes', 'да', 'д']:
        print("❌ Парсинг отменен")
        return
    
    # Запуск парсинга
    print(f"\n🔄 ЗАПУСК ПАРСИНГА")
    print("=" * 30)
    start_time = time.time()
    
    try:
        # Создаем парсер
        parser = OzonParserIntegrated(target_count=target_count)
        
        # Парсинг товаров
        print("\n🛒 ПАРСИНГ ТОВАРОВ OZON")
        print("-" * 25)
        
        products = parser.parse_ozon_products(url, max_products=target_count)
        
        if products:
            end_time = time.time()
            duration = end_time - start_time
            
            # Вычисляем успешность
            success_rate = (len(products) / target_count * 100) if target_count > 0 else 100
            
            print(f"\n✅ ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!")
            print(f"⏱️ Время выполнения: {duration:.1f} секунд")
            
            # Вывод сводки результатов
            print_results_summary(products, target_count, success_rate)
            
            # Создание дашборда
            print(f"\n🎨 СОЗДАНИЕ ДАШБОРДА")
            print("-" * 25)
            
            dashboard_generator = OzonDashboardGenerator()
            
            # Подготавливаем данные для дашборда
            dashboard_data = {
                'products': products,
                'total_count': len(products),
                'target_count': target_count,
                'success_rate': success_rate,
                'session_id': parser.session_id,
                'search_url': url,
                'platform': 'Ozon'
            }
            
            # Генерируем дашборд
            dashboard_file = dashboard_generator.generate_dashboard(dashboard_data)
            
            if dashboard_file:
                print(f"✅ Дашборд создан: {dashboard_file}")
                
                # Предложение открыть дашборд
                open_dashboard = input("\nОткрыть дашборд в браузере? (y/n): ").strip().lower()
                if open_dashboard in ['y', 'yes', 'да', 'д']:
                    try:
                        import webbrowser
                        webbrowser.open(f"file://{os.path.abspath(dashboard_file)}")
                        print("🌐 Дашборд открыт в браузере")
                    except Exception as e:
                        print(f"❌ Ошибка открытия дашборда: {e}")
                        print(f"📁 Откройте файл вручную: {os.path.abspath(dashboard_file)}")
            else:
                print("❌ Ошибка создания дашборда")
        else:
            print(f"\n❌ ПАРСИНГ ЗАВЕРШИЛСЯ БЕЗ РЕЗУЛЬТАТОВ")
            print("Проверьте URL и попробуйте снова")
    
    except KeyboardInterrupt:
        print(f"\n⚠️ ПАРСИНГ ПРЕРВАН ПОЛЬЗОВАТЕЛЕМ")
        print("Частичные результаты сохранены")
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n👋 РАБОТА ЗАВЕРШЕНА")
    print("=" * 30)

if __name__ == "__main__":
    main()
