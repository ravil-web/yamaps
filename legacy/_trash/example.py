#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Пример использования парсера Яндекс Карт
"""

from config import Config
from src.main_parser import YandexMapsParser

def example_single_url():
    """Пример парсинга одного URL"""
    print("🔍 Пример парсинга одного URL")
    print("-" * 40)
    
    # URL для парсинга
    url = "https://yandex.ru/maps/39/rostov-na-donu/search/Ростов%20на%20дону%20суворовский%20стоматология/?ll=39.628128%2C47.254342&sll=39.680726%2C47.244712&sspn=0.239905%2C0.052742&z=10.61"
    
    # Настройка конфигурации
    config = Config()
    config.HEADLESS = False  # Показать браузер для отладки
    config.DELAY_BETWEEN_REQUESTS = 3  # Увеличить задержку
    
    # Создание парсера
    parser = YandexMapsParser(config)
    
    # Парсинг
    result = parser.parse_url(url, max_pages=2, save_format='all')
    
    # Вывод результатов
    if result['success']:
        print(f"✅ Успешно собрано {result['total_businesses']} предприятий")
        print(f"📖 Обработано страниц: {result['pages_processed']}")
        
        # Статистика
        businesses = []  # Здесь должны быть данные из result
        stats = parser.get_statistics(businesses)
        print(f"📊 Статистика: {stats}")
    else:
        print(f"❌ Ошибка: {result['error']}")

def example_multiple_urls():
    """Пример парсинга нескольких URL"""
    print("\n🔍 Пример парсинга нескольких URL")
    print("-" * 40)
    
    # Список URL для парсинга
    urls = [
        "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/",
        "https://yandex.ru/maps/39/rostov-na-donu/search/кафе/",
        "https://yandex.ru/maps/39/rostov-na-donu/search/аптека/"
    ]
    
    # Настройка конфигурации
    config = Config()
    config.HEADLESS = True  # Скрытый режим
    config.DELAY_BETWEEN_REQUESTS = 2
    
    # Создание парсера
    parser = YandexMapsParser(config)
    
    # Парсинг всех URL
    results = parser.parse_multiple_urls(urls, max_pages_per_url=1, save_format='csv')
    
    # Вывод результатов
    total_businesses = 0
    for i, result in enumerate(results, 1):
        if result['success']:
            total_businesses += result['total_businesses']
            print(f"✅ URL {i}: {result['total_businesses']} предприятий")
        else:
            print(f"❌ URL {i}: Ошибка - {result['error']}")
    
    print(f"📈 Всего собрано: {total_businesses} предприятий")

def example_custom_config():
    """Пример с кастомной конфигурацией"""
    print("\n🔍 Пример с кастомной конфигурацией")
    print("-" * 40)
    
    # Создание кастомной конфигурации
    config = Config()
    config.HEADLESS = True
    config.WINDOW_SIZE = (1366, 768)
    config.DELAY_BETWEEN_REQUESTS = 1.5
    config.MAX_RETRIES = 5
    config.CAPTCHA_TIMEOUT = 120
    config.USE_PROXY = False
    config.PROXY_LIST = ['http://proxy1:8080', 'http://proxy2:8080']  # Пример прокси
    
    # URL для парсинга
    url = "https://yandex.ru/maps/39/rostov-na-donu/search/ресторан/"
    
    # Создание парсера
    parser = YandexMapsParser(config)
    
    # Парсинг с сохранением только в Excel
    result = parser.parse_url(url, max_pages=3, save_format='excel')
    
    if result['success']:
        print(f"✅ Собрано {result['total_businesses']} ресторанов")
        print(f"📄 Сохранено в Excel: {result['saved_files'].get('excel', 'N/A')}")

if __name__ == "__main__":
    print("🚀 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ПАРСЕРА ЯНДЕКС КАРТ")
    print("=" * 50)
    
    try:
        # Запуск примеров
        example_single_url()
        example_multiple_urls()
        example_custom_config()
        
        print("\n✅ Все примеры выполнены успешно!")
        
    except KeyboardInterrupt:
        print("\n⏹️ Парсинг прерван пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка выполнения примеров: {e}")
