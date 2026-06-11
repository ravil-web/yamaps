#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ============================================================================
# КОНФИГУРАЦИЯ ПАРСЕРА YANDEX MAPS И OZON
# ============================================================================

# URL для поиска предприятий
SEARCH_URL = "https://yandex.ru/maps/39/rostov-na-donu/search/Кейтеринг/?ll=39.686872%2C47.287867&sctx=ZAAAAAgBEAAaKAoSCaHYCpqW2ENAEZhsPNhiqUdAEhIJDJQUWABTtj8Rgjy7fOvDoj8iBgABAgMEBSgKOABA6IgGSAFiC2ZyZXNobmVzcz0wYhdzb3VyY2U9YnVzaW5lc3M6ZXhwX3JlZmoCcnWdAc3MzD2gAQCoAQC9ATYL1P%2FCAY8BtLSw4MYEvLjP20DO7KWWxASmgMfBuQHrvL7lA9bvvocErtne668G4pvb8NMFzr3Pj9gDwIGP35IDvLXrqNMF%2BOuKo%2F0D1%2BPlkgTtu7nDoAX30%2FfSsQLerKa10gSVlefjBJjZyOvPA%2FG72vOHBIqkgpAF97774oQH3rjZp%2BwGhMTgh4EC9KLXircGxffLwQSCAhLQmtC10LnRgtC10YDQuNC90LOKAgkxODQxMDgzMjGSAgCaAgxkZXNrdG9wLW1hcHOqAgo0MTgxNDA5MTk22gIoChIJ14aKcf7YQ0ARF%2B55NQekR0ASEgkA8wGBzqTZPxEADxE3p5LFP%2BACAQ%3D%3D&sll=39.686872%2C47.287867&sspn=0.230133%2C0.096788&z=12.6"

# Количество предприятий для парсинга (0 = все найденные)
TARGET_BUSINESSES_COUNT = 0

# Количество товаров/услуг для каждого предприятия (0 = все найденные)
TARGET_PRODUCTS_COUNT = 50

# Настройки задержек (в секундах)
DELAYS = {
    'page_load': 5,        # Загрузка страницы
    'scroll': 1,           # Прокрутка
    'tab_switch': 3,       # Переключение вкладок
    'element_click': 2,    # Клик по элементу
    'between_businesses': 3  # Между предприятиями
}

# Настройки браузера
BROWSER_OPTIONS = {
    'window_size': '1920,1080',
    'start_maximized': True,
    'disable_logging': True,
    'log_level': 3
}

# Структура папок
FOLDER_STRUCTURE = {
    'base_folder': 'parsing_results',  # Основная папка для результатов
    'businesses_subfolder': 'businesses',  # Подпапка для предприятий
    'logs_subfolder': 'logs'  # Подпапка для логов
}

# Настройки логирования
LOGGING = {
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
    'file_encoding': 'utf-8',
    'include_timestamp': True
}

# Настройки сохранения
SAVE_OPTIONS = {
    'save_json': True,     # Сохранять JSON файлы
    'save_csv': True,      # Сохранять CSV файлы
    'save_products_separate': True,  # Отдельный CSV для товаров
    'include_timestamp': True  # Включать timestamp в имя файла
}

# Настройки обработки ошибок
ERROR_HANDLING = {
    'continue_on_error': True,  # Продолжать при ошибке предприятия
    'max_retries': 3,           # Максимум попыток для одного предприятия
    'save_on_interrupt': True   # Сохранять данные при прерывании
}

# ============================================================================
# КОНФИГУРАЦИЯ ПАРСЕРА OZON
# ============================================================================

# URL для парсинга Ozon (примеры)
OZON_URLS = {
    'seller_example': 'https://www.ozon.ru/seller/example-seller-123456/',
    'search_books': 'https://www.ozon.ru/search/?text=книги',
    'category_books': 'https://www.ozon.ru/category/knigi-16500/',
    'category_electronics': 'https://www.ozon.ru/category/elektronika-15500/'
}

# Количество товаров для парсинга Ozon (0 = все найденные)
TARGET_OZON_PRODUCTS_COUNT = 20

# Настройки задержек для Ozon (в секундах)
OZON_DELAYS = {
    'page_load': 3,        # Загрузка страницы
    'scroll': 1,           # Прокрутка
    'product_click': 2,    # Клик по товару
    'between_pages': 3,    # Между страницами
    'load_more': 2         # Загрузка дополнительных товаров
}

# Настройки браузера для Ozon
OZON_BROWSER_OPTIONS = {
    'window_size': '1920,1080',
    'start_maximized': True,
    'disable_logging': True,
    'log_level': 3,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Структура папок для Ozon
OZON_FOLDER_STRUCTURE = {
    'base_folder': 'parsing_results',  # Основная папка для результатов
    'ozon_subfolder': 'ozon',          # Подпапка для Ozon
    'dashboard_subfolder': 'dashboard' # Подпапка для дашбордов
}

# Настройки сохранения для Ozon
OZON_SAVE_OPTIONS = {
    'save_json': True,     # Сохранять JSON файлы
    'save_excel': True,    # Сохранять Excel файлы
    'save_dashboard': True, # Создавать дашборд
    'include_timestamp': True  # Включать timestamp в имя файла
}

# Настройки обработки ошибок для Ozon
OZON_ERROR_HANDLING = {
    'continue_on_error': True,  # Продолжать при ошибке товара
    'max_retries': 3,           # Максимум попыток для одного товара
    'save_on_interrupt': True,  # Сохранять данные при прерывании
    'skip_invalid_products': True  # Пропускать товары с неполными данными
}
