#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Генератор дашборда для парсера Ozon
"""

import os
import json
from datetime import datetime
from jinja2 import Template

class OzonDashboardGenerator:
    """Генератор дашборда для Ozon"""
    
    def __init__(self):
        self.template = self.get_dashboard_template()
    
    def get_dashboard_template(self):
        """Шаблон дашборда для Ozon"""
        return Template("""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Дашборд парсинга Ozon - {{ session_id }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card h3 {
            color: #333;
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        
        .stat-card .number {
            font-size: 2.5em;
            font-weight: bold;
            color: #ff6b6b;
            margin-bottom: 5px;
        }
        
        .stat-card .label {
            color: #666;
            font-size: 0.9em;
        }
        
        .content {
            padding: 30px;
        }
        
        .search-info {
            background: #e3f2fd;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            border-left: 5px solid #2196f3;
        }
        
        .search-info h3 {
            color: #1976d2;
            margin-bottom: 10px;
        }
        
        .search-info p {
            color: #333;
            margin: 5px 0;
        }
        
        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .product-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 1px solid #e0e0e0;
        }
        
        .product-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.15);
        }
        
        .product-name {
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
            line-height: 1.4;
        }
        
        .product-price {
            font-size: 1.5em;
            font-weight: bold;
            color: #ff6b6b;
            margin-bottom: 10px;
        }
        
        .product-rating {
            color: #ffa726;
            margin-bottom: 10px;
            font-weight: 500;
        }
        
        .product-reviews {
            color: #666;
            margin-bottom: 10px;
            font-size: 0.9em;
        }
        
        .product-delivery {
            color: #4caf50;
            margin-bottom: 15px;
            font-weight: 500;
        }
        
        .product-link {
            display: inline-block;
            background: #ff6b6b;
            color: white;
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 20px;
            font-size: 0.9em;
            transition: background 0.3s ease;
        }
        
        .product-link:hover {
            background: #ee5a24;
        }
        
        .filters {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        
        .filter-group {
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .filter-group label {
            font-weight: 500;
            color: #333;
        }
        
        .filter-group input, .filter-group select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        
        .filter-group button {
            background: #ff6b6b;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .filter-group button:hover {
            background: #ee5a24;
        }
        
        .summary {
            background: #e8f5e8;
            padding: 20px;
            border-radius: 10px;
            margin-top: 30px;
            border-left: 5px solid #4caf50;
        }
        
        .summary h3 {
            color: #2e7d32;
            margin-bottom: 10px;
        }
        
        .summary p {
            color: #333;
            margin: 5px 0;
        }
        
        .footer {
            background: #333;
            color: white;
            text-align: center;
            padding: 20px;
        }
        
        .no-products {
            text-align: center;
            padding: 50px;
            color: #666;
            font-size: 1.2em;
        }
        
        @media (max-width: 768px) {
            .products-grid {
                grid-template-columns: 1fr;
            }
            
            .stats {
                grid-template-columns: 1fr;
            }
            
            .filter-group {
                flex-direction: column;
                align-items: stretch;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛒 Дашборд парсинга Ozon</h1>
            <p>Результаты парсинга от {{ datetime.now().strftime('%d.%m.%Y %H:%M') }}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>Всего товаров</h3>
                <div class="number">{{ total_count }}</div>
                <div class="label">найдено</div>
            </div>
            <div class="stat-card">
                <h3>Целевое количество</h3>
                <div class="number">{{ target_count }}</div>
                <div class="label">запрошено</div>
            </div>
            <div class="stat-card">
                <h3>Успешность</h3>
                <div class="number">{{ "%.1f"|format(success_rate) }}%</div>
                <div class="label">выполнено</div>
            </div>
            <div class="stat-card">
                <h3>Сессия</h3>
                <div class="number">{{ session_id }}</div>
                <div class="label">ID</div>
            </div>
        </div>
        
        <div class="content">
            <div class="search-info">
                <h3>📋 Информация о парсинге</h3>
                <p><strong>URL:</strong> {{ search_url }}</p>
                <p><strong>Платформа:</strong> {{ platform }}</p>
                <p><strong>Время парсинга:</strong> {{ datetime.now().strftime('%d.%m.%Y %H:%M:%S') }}</p>
                <p><strong>Статус:</strong> {% if success_rate >= 80 %}✅ Успешно{% elif success_rate >= 50 %}⚠️ Частично{% else %}❌ Неудачно{% endif %}</p>
            </div>
            
            {% if products %}
            <div class="filters">
                <div class="filter-group">
                    <label for="search">🔍 Поиск:</label>
                    <input type="text" id="search" placeholder="Введите название товара...">
                    <label for="sort">📊 Сортировка:</label>
                    <select id="sort">
                        <option value="name">По названию</option>
                        <option value="price">По цене</option>
                        <option value="rating">По рейтингу</option>
                    </select>
                    <button onclick="filterProducts()">Применить</button>
                </div>
            </div>
            
            <div class="products-grid" id="productsGrid">
                {% for product in products %}
                <div class="product-card" data-name="{{ product.name|lower }}" data-price="{{ product.price|replace(' ', '')|replace('₽', '')|replace(',', '')|int if product.price.isdigit() else 0 }}" data-rating="{{ product.rating|replace('•', '')|replace('отзыв', '')|replace('отзывов', '')|replace('отзыва', '')|strip|int if product.rating.replace('.', '').replace('•', '').replace('отзыв', '').replace('отзывов', '').replace('отзыва', '').strip().isdigit() else 0 }}">
                    <div class="product-name">{{ product.name }}</div>
                    <div class="product-price">{{ product.price }} ₽</div>
                    <div class="product-rating">⭐ {{ product.rating }}</div>
                    <div class="product-reviews">💬 {{ product.reviews }}</div>
                    <div class="product-delivery">🚚 {{ product.delivery }}</div>
                    {% if product.link and product.link != 'Ссылка не найдена' %}
                    <a href="{{ product.link }}" target="_blank" class="product-link">Открыть товар</a>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% else %}
            <div class="no-products">
                <h3>😔 Товары не найдены</h3>
                <p>Попробуйте изменить параметры поиска или проверьте URL</p>
            </div>
            {% endif %}
            
            <div class="summary">
                <h3>📊 Сводка результатов</h3>
                <p><strong>Всего обработано:</strong> {{ total_count }} товаров</p>
                <p><strong>Целевое количество:</strong> {{ target_count }} товаров</p>
                <p><strong>Процент выполнения:</strong> {{ "%.1f"|format(success_rate) }}%</p>
                <p><strong>Время создания дашборда:</strong> {{ datetime.now().strftime('%d.%m.%Y %H:%M:%S') }}</p>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2024 Парсер Ozon | Создано автоматически</p>
        </div>
    </div>
    
    <script>
        function filterProducts() {
            const searchTerm = document.getElementById('search').value.toLowerCase();
            const sortBy = document.getElementById('sort').value;
            const productsGrid = document.getElementById('productsGrid');
            const productCards = Array.from(productsGrid.children);
            
            // Фильтрация
            let filteredCards = productCards.filter(card => {
                const name = card.dataset.name;
                return name.includes(searchTerm);
            });
            
            // Сортировка
            filteredCards.sort((a, b) => {
                let aValue, bValue;
                
                switch(sortBy) {
                    case 'name':
                        aValue = a.dataset.name;
                        bValue = b.dataset.name;
                        return aValue.localeCompare(bValue);
                    case 'price':
                        aValue = parseInt(a.dataset.price) || 0;
                        bValue = parseInt(b.dataset.price) || 0;
                        return bValue - aValue;
                    case 'rating':
                        aValue = parseInt(a.dataset.rating) || 0;
                        bValue = parseInt(b.dataset.rating) || 0;
                        return bValue - aValue;
                    default:
                        return 0;
                }
            });
            
            // Обновление отображения
            productsGrid.innerHTML = '';
            filteredCards.forEach(card => {
                productsGrid.appendChild(card);
            });
        }
        
        // Автоматическая фильтрация при вводе
        document.getElementById('search').addEventListener('input', filterProducts);
        document.getElementById('sort').addEventListener('change', filterProducts);
    </script>
</body>
</html>
        """)
    
    def generate_dashboard(self, parser_results, output_file=None):
        """Генерация дашборда"""
        try:
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"dashboard/ozon_dashboard_{timestamp}.html"
            
            # Создаем папку dashboard если её нет
            os.makedirs("dashboard", exist_ok=True)
            
            # Подготавливаем данные для шаблона
            template_data = {
                'products': parser_results.get('products', []),
                'total_count': parser_results.get('total_count', 0),
                'target_count': parser_results.get('target_count', 0),
                'success_rate': parser_results.get('success_rate', 0),
                'session_id': parser_results.get('session_id', 'unknown'),
                'search_url': parser_results.get('search_url', ''),
                'platform': parser_results.get('platform', 'Ozon'),
                'datetime': datetime
            }
            
            # Генерируем HTML
            html_content = self.template.render(**template_data)
            
            # Сохраняем файл
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ Дашборд создан: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Ошибка создания дашборда: {e}")
            return None

def main():
    """Основная функция для тестирования"""
    print("🚀 Генератор дашборда Ozon запущен")
    
    # Тестовые данные
    test_data = {
        'products': [
            {
                'name': 'Тестовый товар 1',
                'price': '1234',
                'rating': '4.8 • 123 отзыва',
                'reviews': '4.8 • 123 отзыва',
                'delivery': 'Завтра',
                'link': 'https://example.com/product1'
            },
            {
                'name': 'Тестовый товар 2',
                'price': '5678',
                'rating': '4.5 • 89 отзывов',
                'reviews': '4.5 • 89 отзывов',
                'delivery': 'Сегодня',
                'link': 'https://example.com/product2'
            }
        ],
        'total_count': 2,
        'target_count': 10,
        'success_rate': 20.0,
        'session_id': 'test_20241208_120000',
        'search_url': 'https://www.ozon.ru/seller/test-seller/',
        'platform': 'Ozon'
    }
    
    generator = OzonDashboardGenerator()
    dashboard_file = generator.generate_dashboard(test_data)
    
    if dashboard_file:
        print(f"🎉 Дашборд успешно создан: {dashboard_file}")
    else:
        print("❌ Ошибка создания дашборда")

if __name__ == "__main__":
    main()
