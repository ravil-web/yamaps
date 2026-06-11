# Параллельный парсер Ozon

## Обзор

Параллельный парсер Ozon создан для получения таких же результатов, как в оригинальном проекте `ozon_simple`. Парсер поддерживает два режима работы:

1. **Быстрый парсинг товаров** - извлечение базовой информации о товарах
2. **Детальный парсинг** - получение полной информации о товарах

## Структура проекта

### Основные файлы

- `ozon_parallel_parser.py` - основной класс парсера
- `run_ozon_parallel.py` - файл запуска с интерфейсом
- `test_ozon_parallel.py` - тесты для проверки функциональности
- `ПАРАЛЛЕЛЬНЫЙ_ПАРСЕР_OZON.md` - данная документация

### Интегрированные возможности

- **Парсинг товаров продавцов** - извлечение списка товаров
- **Детальный парсинг** - получение полной информации о товарах
- **Автоматическая прокрутка** - загрузка контента
- **Пагинация** - переход между страницами
- **Сохранение результатов** - в JSON формате

## Возможности

### 🛒 Парсинг товаров продавца
- Извлечение названий товаров
- Получение цен
- Сбор рейтингов и отзывов
- Извлечение ссылок на товары
- Информация о доставке

### 📝 Детальный парсинг
- Полная информация о товаре
- Описание товара
- Характеристики
- Информация о продавце
- SKU товара
- URL товара

### 🔧 Технические возможности
- Автоматическое определение селекторов
- Обход блокировок
- Случайные задержки
- Обработка ошибок
- Сохранение результатов

## Установка

### 1. Установка зависимостей

```bash
pip install selenium==4.15.2
pip install webdriver-manager==4.0.1
pip install fake-useragent==1.4.0
```

### 2. Проверка установки

```bash
python test_ozon_parallel.py
```

## Использование

### 1. Запуск через интерфейс

```bash
python run_ozon_parallel.py
```

### 2. Программный запуск

```python
from ozon_parallel_parser import OzonParallelParser

# Создание парсера
parser = OzonParallelParser(headless=False)

# Парсинг товаров продавца
products = parser.parse_seller_products(
    "https://www.ozon.ru/seller/example-seller-123456/",
    max_products=20,
    max_pages=3
)

# Парсинг с детальной информацией
detailed_products = parser.parse_products_with_details(
    "https://www.ozon.ru/seller/example-seller-123456/",
    max_products=5,
    max_pages=1
)

# Сохранение результатов
parser.save_results(products, "seller_products")
parser.save_results(detailed_products, "seller_detailed_products")

# Закрытие парсера
parser.close()
```

## Структура данных

### Товары продавца
```json
{
  "name": "Название товара",
  "price": "1234",
  "rating": "4.8 • 123 отзыва",
  "reviews": "4.8 • 123 отзыва",
  "link": "https://www.ozon.ru/product/...",
  "delivery": "Завтра"
}
```

### Детальная информация
```json
{
  "name": "Название товара",
  "price": "1234",
  "rating": "4.8 • 123 отзыва",
  "reviews": "4.8 • 123 отзыва",
  "description": "Подробное описание товара...",
  "specifications": "Характеристики товара",
  "delivery": "Информация о доставке",
  "seller": "Название продавца",
  "sku": "1234567890",
  "url": "https://www.ozon.ru/product/..."
}
```

## Примеры URL

### Продавцы
```
https://www.ozon.ru/seller/example-seller-123456/
https://www.ozon.ru/seller/another-seller-789012/
```

### Категории
```
https://www.ozon.ru/category/knigi-16500/
https://www.ozon.ru/category/elektronika-15500/
```

### Поиск
```
https://www.ozon.ru/search/?text=книги
https://www.ozon.ru/search/?text=смартфоны
```

## Тестирование

### Запуск тестов

```bash
python test_ozon_parallel.py
```

### Доступные тесты

1. **Тест парсинга товаров продавца** - проверка базового парсинга
2. **Тест парсинга с детальной информацией** - проверка детального парсинга
3. **Тест сравнения структуры данных** - сравнение с оригинальными данными

## Результаты

### Структура папок

```
parsing_results/
├── session_YYYYMMDD_HHMMSS/
│   ├── seller_products.json
│   ├── seller_detailed_products.json
│   └── parsing_log.txt
```

### Форматы экспорта

- **JSON** - структурированные данные
- **Логи** - информация о процессе парсинга

## Сравнение с оригиналом

### Соответствие структуры данных

Парсер создан для получения точно таких же результатов, как в оригинальном проекте:

- **Поля товаров**: `name`, `price`, `rating`, `reviews`, `link`, `delivery`
- **Поля детальной информации**: `name`, `price`, `rating`, `reviews`, `description`, `specifications`, `delivery`, `seller`, `sku`, `url`

### Селекторы

Используются актуальные селекторы Ozon:
- Название: `span[class*="tsBody500Medium"]`
- Цена: `span[class*="tsHeadline500Medium"]`
- Рейтинг: `span[style*="color: rgb(255, 165, 0)"]`
- И другие актуальные селекторы

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

3. **Товары не найдены**
   - Проверьте URL продавца
   - Убедитесь, что страница загружается
   - Проверьте селекторы

### Отладка

```python
# Включение отладочного режима
parser = OzonParallelParser(headless=False)
parser.debug_mode = True
```

## Производительность

### Оптимизация

- Используйте `headless=True` для ускорения
- Ограничивайте количество товаров
- Настройте задержки между запросами
- Используйте кэширование

### Рекомендации

- **Быстрый парсинг**: до 50 товаров за 2-3 минуты
- **Детальный парсинг**: до 10 товаров за 5-10 минут
- **Память**: ~100MB для 100 товаров

## Безопасность

### Рекомендации

- Соблюдайте robots.txt
- Не превышайте лимиты запросов
- Используйте случайные задержки
- Соблюдайте условия использования Ozon

### Настройки безопасности

```python
# Случайные задержки
time.sleep(random.uniform(2, 4))

# Ротация User-Agent
self.options.add_argument("user-agent=Mozilla/5.0...")

# Обход блокировок
self.options.add_argument('--disable-blink-features=AutomationControlled')
```

## Расширение функциональности

### Добавление новых полей

```python
def _extract_product_data(self, card):
    product = {}
    
    # Добавление нового поля
    new_field_selectors = [
        'span[class*="new-field"]',
        'div[class*="new-field"]'
    ]
    product['new_field'] = self._extract_text(card, new_field_selectors, 'По умолчанию')
    
    return product
```

### Кастомизация селекторов

```python
# Обновление селекторов в методе _extract_product_data
name_selectors = [
    'span[class*="tsBody500Medium"]',
    'span[class*="new-selector"]',  # Новый селектор
    'a[href*="/product/"] span[class*="tsBody"]'
]
```

## Мониторинг

### Логирование

```python
# Включение подробного логирования
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Метрики

- Количество обработанных товаров
- Время выполнения
- Количество ошибок
- Успешность парсинга

## Лицензия

Этот парсер предназначен для образовательных и исследовательских целей. Соблюдайте условия использования Ozon и применимое законодательство.

---

**Готово!** Параллельный парсер Ozon создан и готов к использованию.
