# Интеграция парсера Ozon в универсальный парсер

## Обзор

Универсальный парсер объединяет функциональность парсера Яндекс.Карт и парсера Ozon в единое решение, позволяющее парсить данные с обеих платформ.

## Структура проекта

### Основные файлы

- `universal_parser.py` - основной класс универсального парсера
- `config_universal.py` - конфигурация для всех платформ
- `run_universal_parser.py` - файл запуска с интерфейсом
- `test_universal_parser.py` - тесты для всех платформ
- `requirements_parser.txt` - обновленные зависимости

### Интегрированные парсеры

- **Яндекс.Карты** - парсинг предприятий и их данных
- **Ozon** - парсинг товаров продавцов и поисковых результатов

## Возможности

### 🗺️ Яндекс.Карты
- Парсинг предприятий по поисковым запросам
- Извлечение контактной информации
- Получение рейтингов и отзывов
- Автоматическая прокрутка для загрузки контента

### 🛒 Ozon
- Парсинг товаров продавцов
- Парсинг результатов поиска
- Извлечение цен и рейтингов
- Поддержка пагинации

### 🔧 Универсальные функции
- Автоматическое определение платформы по URL
- Единый интерфейс для всех платформ
- Гибкая конфигурация
- Сохранение результатов в различных форматах

## Установка

### 1. Установка зависимостей

```bash
pip install -r requirements_parser.txt
```

### 2. Проверка установки

```bash
python test_universal_parser.py
```

## Использование

### 1. Запуск через интерфейс

```bash
python run_universal_parser.py
```

### 2. Программный запуск

```python
from universal_parser import UniversalParser

# Создание парсера
parser = UniversalParser(headless=False, target_count=10)

# Парсинг Яндекс.Карт
yandex_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/"
success = parser.parse(yandex_url)

# Парсинг Ozon
ozon_url = "https://www.ozon.ru/seller/example-seller-123456/"
success = parser.parse(ozon_url)

# Закрытие парсера
parser.close()
```

## Конфигурация

### Основные настройки

```python
# config_universal.py

# Количество элементов для парсинга
TARGET_COUNT = 0  # 0 = все найденные

# Режим работы браузера
HEADLESS_MODE = False

# Настройки прокрутки
MAX_SCROLL_ATTEMPTS = 5
SCROLL_DELAY = 1.5
```

### Настройки платформ

```python
# Яндекс.Карты
YANDEX_MAPS = {
    'enabled': True,
    'max_businesses': 50,
    'scroll_attempts': 5,
    'wait_timeout': 10
}

# Ozon
OZON = {
    'enabled': True,
    'max_products': 100,
    'scroll_attempts': 3,
    'wait_timeout': 15
}
```

## Примеры URL

### Яндекс.Карты
```
https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/?ll=39.806284%2C47.275656&z=12
https://yandex.ru/maps/39/rostov-na-donu/search/кафе/?ll=39.806284%2C47.275656&z=12
https://yandex.ru/maps/39/rostov-na-donu/search/магазины/?ll=39.806284%2C47.275656&z=12
```

### Ozon
```
https://www.ozon.ru/seller/example-seller-123456/
https://www.ozon.ru/category/knigi-16500/
https://www.ozon.ru/search/?text=книги
```

## Структура данных

### Предприятия (Яндекс.Карты)
```json
{
  "name": "Название предприятия",
  "address": "Адрес",
  "phone": "+7 (999) 123-45-67",
  "website": "https://example.com",
  "rating": "4.5",
  "reviews_count": "123",
  "working_hours": "Пн-Пт 9:00-18:00",
  "description": "Описание",
  "url": "https://yandex.ru/maps/org/..."
}
```

### Товары (Ozon)
```json
{
  "name": "Название товара",
  "price": "1234 ₽",
  "rating": "4.8",
  "reviews": "567 отзывов",
  "link": "https://www.ozon.ru/product/...",
  "delivery": "Завтра"
}
```

## Тестирование

### Запуск тестов

```bash
python test_universal_parser.py
```

### Доступные тесты

1. **Тест определения платформы** - проверка автоматического определения платформы по URL
2. **Тест конфигурации** - проверка загрузки настроек
3. **Тест сохранения результатов** - проверка сохранения данных
4. **Тест парсинга Яндекс.Карт** - полный тест парсинга предприятий
5. **Тест парсинга Ozon** - полный тест парсинга товаров

## Результаты

### Структура папок

```
parsing_results/
├── session_YYYYMMDD_HHMMSS/
│   ├── results.json
│   ├── parsing_log.txt
│   └── summary.txt
dashboard/
├── dashboard_YYYYMMDD_HHMMSS.html
└── modern_dashboard_YYYYMMDD_HHMMSS.html
output/
└── results_YYYYMMDD_HHMMSS.xlsx
```

### Форматы экспорта

- **JSON** - структурированные данные
- **Excel** - таблицы для анализа
- **HTML** - интерактивные дашборды
- **CSV** - простые таблицы

## Устранение проблем

### Частые ошибки

1. **ChromeDriver не найден**
   ```bash
   pip install --upgrade webdriver-manager
   ```

2. **Блокировка сайтом**
   - Увеличьте задержки между запросами
   - Используйте прокси
   - Включите ротацию User-Agent

3. **Медленная работа**
   - Установите `HEADLESS_MODE = True`
   - Уменьшите `TARGET_COUNT`
   - Закройте другие программы

### Отладка

```python
# Включение отладочного режима
parser = UniversalParser(headless=False, target_count=5)
parser.debug_mode = True
```

## Расширение функциональности

### Добавление новой платформы

1. Добавьте платформу в `SUPPORTED_PLATFORMS`
2. Создайте метод `parse_new_platform()`
3. Добавьте селекторы в конфигурацию
4. Обновите `detect_platform()`

### Кастомизация селекторов

```python
# config_universal.py
NEW_PLATFORM = {
    'enabled': True,
    'selectors': {
        'item_cards': ["//div[@class='item']"],
        'item_name': ".//h3[@class='title']",
        'item_price': ".//span[@class='price']"
    }
}
```

## Производительность

### Оптимизация

- Используйте `headless=True` для ускорения
- Ограничивайте `TARGET_COUNT`
- Настройте задержки между запросами
- Используйте кэширование

### Мониторинг

```python
# Включение мониторинга
MONITORING_ENABLED = True
METRICS_ENABLED = True
PERFORMANCE_TRACKING = True
```

## Безопасность

### Рекомендации

- Используйте прокси для больших объемов
- Соблюдайте robots.txt
- Не превышайте лимиты запросов
- Используйте случайные задержки

### Настройки безопасности

```python
SECURITY = {
    'enable_ssl_verification': True,
    'enable_csrf_protection': True,
    'rate_limit': 100,  # запросов в минуту
    'max_request_size': 10485760  # 10MB
}
```

## Лицензия

Этот парсер предназначен для образовательных и исследовательских целей. Соблюдайте условия использования сайтов и применимое законодательство.

---

**Готово!** Универсальный парсер интегрирован и готов к использованию.
