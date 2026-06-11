#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ============================================================================
# КОНФИГУРАЦИЯ УНИВЕРСАЛЬНОГО ПАРСЕРА
# ============================================================================

# === ОСНОВНЫЕ НАСТРОЙКИ ===
# Количество элементов для парсинга (0 = все найденные)
TARGET_COUNT = 0

# Поддерживаемые платформы
SUPPORTED_PLATFORMS = ['yandex_maps', 'ozon']

# === НАСТРОЙКИ БРАУЗЕРА ===
HEADLESS_MODE = False  # True для работы без окна браузера
BROWSER_TIMEOUT = 30   # Таймаут ожидания элементов (секунды)
WINDOW_SIZE = "1920,1080"  # Размер окна браузера

# === НАСТРОЙКИ ПРОКРУТКИ ===
SCROLL_DELAY = 1.5     # Задержка между прокрутками (секунды)
MAX_SCROLL_ATTEMPTS = 5  # Максимальное количество попыток прокрутки
SCROLL_STEP = 1000     # Шаг прокрутки в пикселях

# === НАСТРОЙКИ ПАРСИНГА ===
MAX_RETRIES = 3        # Максимальное количество повторных попыток
RETRY_DELAY = 2        # Задержка между повторными попытками (секунды)
REQUEST_DELAY = (2, 4) # Случайная задержка между запросами (мин, макс)

# === НАСТРОЙКИ СОХРАНЕНИЯ ===
SAVE_JSON = True       # Сохранение в JSON формате
SAVE_EXCEL = True      # Сохранение в Excel формате
SAVE_DASHBOARD = True  # Создание HTML дашборда
SAVE_CSV = False       # Сохранение в CSV формате

# === НАСТРОЙКИ ДАШБОРДА ===
DASHBOARD_TITLE = "Результаты парсинга"
DASHBOARD_THEME = "modern"  # modern, classic, dark
DASHBOARD_AUTO_OPEN = False # Автоматическое открытие дашборда

# === НАСТРОЙКИ ЛОГИРОВАНИЯ ===
LOG_LEVEL = "INFO"     # DEBUG, INFO, WARNING, ERROR
LOG_TO_FILE = True     # Сохранение логов в файл
LOG_TO_CONSOLE = True  # Вывод логов в консоль
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# === НАСТРОЙКИ ПРОИЗВОДИТЕЛЬНОСТИ ===
ENABLE_CACHING = True  # Включение кэширования
CACHE_TTL = 3600       # Время жизни кэша (секунды)
MAX_CONCURRENT_REQUESTS = 5  # Максимальное количество одновременных запросов

# === НАСТРОЙКИ БЕЗОПАСНОСТИ ===
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
PROXY_ENABLED = False  # Использование прокси
PROXY_LIST = []        # Список прокси серверов
ROTATE_USER_AGENTS = False  # Ротация User-Agent

# === НАСТРОЙКИ УВЕДОМЛЕНИЙ ===
ENABLE_NOTIFICATIONS = False  # Включение уведомлений
NOTIFICATION_EMAIL = ""       # Email для уведомлений
NOTIFICATION_TELEGRAM = ""    # Telegram для уведомлений
NOTIFICATION_WEBHOOK = ""     # Webhook для уведомлений

# === НАСТРОЙКИ БАЗЫ ДАННЫХ ===
DATABASE_ENABLED = False      # Включение сохранения в БД
DATABASE_URL = ""            # URL подключения к БД
DATABASE_TABLE = "results"   # Название таблицы
DATABASE_BATCH_SIZE = 100    # Размер пакета для вставки

# === НАСТРОЙКИ API ===
API_ENABLED = False          # Включение API
API_PORT = 8000             # Порт для API
API_HOST = "localhost"      # Хост для API
API_AUTH_REQUIRED = False   # Требуется ли аутентификация

# === НАСТРОЙКИ МОНИТОРИНГА ===
MONITORING_ENABLED = False   # Включение мониторинга
METRICS_ENABLED = False      # Включение метрик
HEALTH_CHECK_ENABLED = False # Включение проверки здоровья
PERFORMANCE_TRACKING = False # Отслеживание производительности

# === НАСТРОЙКИ ПЛАТФОРМ ===

# Яндекс.Карты
YANDEX_MAPS = {
    'enabled': True,
    'max_businesses': 50,
    'scroll_attempts': 5,
    'wait_timeout': 10,
    'selectors': {
        'business_links': [
            "//a[contains(@href, '/org/')]",
            "//a[contains(@class, 'search-snippet-view')]",
            "//a[contains(@class, 'business-snippet-view')]"
        ],
        'business_name': "//h1[contains(@class, 'orgpage-header-view__header')]",
        'business_address': "//span[contains(@class, 'orgpage-header-view__address')]",
        'business_phone': "//a[contains(@href, 'tel:')]",
        'business_rating': "//span[contains(@class, 'rating-view__rating')]"
    }
}

# Ozon
OZON = {
    'enabled': True,
    'max_products': 100,
    'scroll_attempts': 3,
    'wait_timeout': 15,
    'selectors': {
        'product_cards': [
            "//div[contains(@class, 'tile-root')]",
            "//div[contains(@class, 'product-card')]",
            "//div[contains(@class, 'item-card')]"
        ],
        'product_name': ".//a[contains(@class, 'tile-hover-target')]",
        'product_price': ".//span[contains(@class, 'tsBody500Medium')]",
        'product_rating': ".//span[contains(@class, 'tsBodyControl400Small')]",
        'product_link': ".//a[contains(@class, 'tile-hover-target')]"
    }
}

# === НАСТРОЙКИ ФИЛЬТРАЦИИ ===
FILTER_ENABLED = False       # Включение фильтрации
FILTER_KEYWORDS = []         # Ключевые слова для фильтрации
FILTER_EXCLUDE_KEYWORDS = [] # Ключевые слова для исключения
FILTER_MIN_RATING = 0        # Минимальный рейтинг
FILTER_MAX_PRICE = 0         # Максимальная цена (0 = без ограничений)

# === НАСТРОЙКИ ЭКСПОРТА ===
EXPORT_FORMATS = ['json', 'excel', 'html']  # Доступные форматы экспорта
EXPORT_INCLUDE_IMAGES = False  # Включение изображений в экспорт
EXPORT_COMPRESS = False        # Сжатие экспортируемых файлов

# === НАСТРОЙКИ ОБНОВЛЕНИЯ ===
AUTO_UPDATE_ENABLED = False   # Автоматическое обновление
UPDATE_CHECK_INTERVAL = 86400 # Интервал проверки обновлений (секунды)
UPDATE_CHANNEL = "stable"     # Канал обновлений (stable, beta, alpha)

# === НАСТРОЙКИ ОТЛАДКИ ===
DEBUG_MODE = False           # Режим отладки
DEBUG_SAVE_SCREENSHOTS = False # Сохранение скриншотов при ошибках
DEBUG_SAVE_HTML = False      # Сохранение HTML при ошибках
DEBUG_VERBOSE = False        # Подробный вывод отладочной информации

# === ПРИМЕРЫ URL ===
EXAMPLE_URLS = {
    'yandex_maps': [
        "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/?ll=39.806284%2C47.275656&z=12",
        "https://yandex.ru/maps/39/rostov-na-donu/search/кафе/?ll=39.806284%2C47.275656&z=12",
        "https://yandex.ru/maps/39/rostov-na-donu/search/магазины/?ll=39.806284%2C47.275656&z=12"
    ],
    'ozon': [
        "https://www.ozon.ru/seller/example-seller-123456/",
        "https://www.ozon.ru/category/knigi-16500/",
        "https://www.ozon.ru/search/?text=книги"
    ]
}

# === НАСТРОЙКИ ПРОИЗВОДИТЕЛЬНОСТИ ===
PERFORMANCE = {
    'enable_multiprocessing': False,  # Включение многопроцессорности
    'max_workers': 4,                 # Максимальное количество воркеров
    'chunk_size': 10,                 # Размер чанка для обработки
    'memory_limit': 1024,             # Лимит памяти в МБ
    'cpu_limit': 80                   # Лимит использования CPU в %
}

# === НАСТРОЙКИ БЕЗОПАСНОСТИ ===
SECURITY = {
    'enable_ssl_verification': True,  # Проверка SSL сертификатов
    'enable_csrf_protection': True,   # Защита от CSRF
    'enable_xss_protection': True,    # Защита от XSS
    'max_request_size': 10485760,     # Максимальный размер запроса (10MB)
    'rate_limit': 100                 # Лимит запросов в минуту
}

# === НАСТРОЙКИ КЭШИРОВАНИЯ ===
CACHE = {
    'enabled': True,
    'backend': 'memory',              # memory, redis, file
    'ttl': 3600,                      # Время жизни кэша в секундах
    'max_size': 1000,                 # Максимальный размер кэша
    'cleanup_interval': 300           # Интервал очистки кэша в секундах
}

# === НАСТРОЙКИ УВЕДОМЛЕНИЙ ===
NOTIFICATIONS = {
    'enabled': False,
    'providers': ['email', 'telegram', 'webhook'],
    'email': {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': '',
        'password': '',
        'from_email': '',
        'to_emails': []
    },
    'telegram': {
        'bot_token': '',
        'chat_id': ''
    },
    'webhook': {
        'url': '',
        'headers': {},
        'timeout': 30
    }
}
