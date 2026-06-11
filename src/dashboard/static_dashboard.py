#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Генератор статического HTML дашборда
"""

import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.offline as pyo
from datetime import datetime
import glob
import re
from src.config import *

class StaticDashboardGenerator:
    def __init__(self, session_folder=None):
        if session_folder:
            # Работаем с конкретной сессией
            self.data_folder = session_folder
            self.businesses_folder = f"{session_folder}/businesses"
        else:
            # Работаем со всеми данными (старый режим)
            self.data_folder = FOLDER_STRUCTURE['base_folder']
            self.businesses_folder = f"{self.data_folder}/{FOLDER_STRUCTURE['businesses_subfolder']}"
        
        self.businesses_data = []
        self.products_data = []
        self.raw_data = {}
        
    def load_all_data(self):
        """Загрузка всех данных из папок парсинга"""
        print("📊 Загрузка данных для дашборда...")
        
        if not os.path.exists(self.businesses_folder):
            print(f"❌ Папка данных не найдена: {self.businesses_folder}")
            return False
            
        business_folders = glob.glob(f"{self.businesses_folder}/*/")
        
        for folder in business_folders:
            try:
                # Берем самый новый JSON файл
                json_files = sorted(glob.glob(f"{folder}/*.json"), key=os.path.getmtime, reverse=True)
                if not json_files:
                    continue
                
                json_file = json_files[0]
                
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                yandex_id = data.get('yandex_id', '')
                self.raw_data[yandex_id] = data
                
                # Обработка цен
                prices = []
                for product in data.get('products_and_services', []):
                    price_str = product.get('price', '')
                    if price_str:
                        numbers = re.findall(r'\d+', price_str.replace(' ', ''))
                        if numbers:
                            prices.append(int(numbers[0]))
                
                # Данные предприятия
                business_info = {
                    'name': data.get('name', 'Неизвестно'),
                    'url': data.get('url', ''),
                    'yandex_id': yandex_id,
                    'rating': data.get('rating', 'Нет рейтинга'),
                    'address': data.get('address', 'Адрес не указан'),
                    'categories': data.get('categories', []),
                    'phones': data.get('phones', []),
                    'website': data.get('website', ''),
                    'extraction_date': data.get('extraction_date', ''),
                    'products_count': len(data.get('products_and_services', [])),
                    'min_price': min(prices) if prices else 0,
                    'max_price': max(prices) if prices else 0,
                    'avg_price': round(sum(prices) / len(prices)) if prices else 0
                }
                self.businesses_data.append(business_info)
                
                # Данные товаров/услуг
                for product in data.get('products_and_services', []):
                    price_str = product.get('price', '')
                    price_num = 0
                    if price_str:
                        numbers = re.findall(r'\d+', price_str.replace(' ', ''))
                        if numbers:
                            price_num = int(numbers[0])
                    
                    product_info = {
                        'business_name': data.get('name', 'Неизвестно'),
                        'business_url': data.get('url', ''),
                        'title': product.get('title', ''),
                        'price': product.get('price', ''),
                        'price_num': price_num,
                        'description': product.get('description', ''),
                        'categories': data.get('categories', [])
                    }
                    self.products_data.append(product_info)
                    
            except Exception as e:
                print(f"❌ Ошибка загрузки {folder}: {e}")
                continue
        
        print(f"✅ Загружено {len(self.businesses_data)} предприятий и {len(self.products_data)} товаров/услуг")
        return len(self.businesses_data) > 0
    
    def create_statistics_charts(self):
        """Создание графиков статистики"""
        charts_html = ""
        
        if not self.businesses_data:
            return charts_html
        
        # График по количеству товаров/услуг
        df_businesses = pd.DataFrame(self.businesses_data)
        top_businesses = df_businesses.nlargest(10, 'products_count')
        
        fig1 = px.bar(
            top_businesses,
            x='name',
            y='products_count',
            title='ТОП-10 предприятий по количеству услуг',
            labels={'name': 'Предприятие', 'products_count': 'Количество услуг'},
            color='products_count',
            color_continuous_scale='viridis'
        )
        fig1.update_xaxes(tickangle=45)
        fig1.update_layout(height=500)
        
        # График средних цен
        price_businesses = df_businesses[df_businesses['avg_price'] > 0].nlargest(10, 'avg_price')
        
        fig2 = px.bar(
            price_businesses,
            x='name',
            y='avg_price',
            title='ТОП-10 предприятий по средней цене услуг',
            labels={'name': 'Предприятие', 'avg_price': 'Средняя цена (₽)'},
            color='avg_price',
            color_continuous_scale='plasma'
        )
        fig2.update_xaxes(tickangle=45)
        fig2.update_layout(height=500)
        
        # Распределение цен
        prices = [p['price_num'] for p in self.products_data if p['price_num'] > 0]
        if prices:
            fig3 = px.histogram(
                x=prices,
                nbins=30,
                title='Распределение цен на услуги',
                labels={'x': 'Цена (₽)', 'y': 'Количество услуг'}
            )
            fig3.update_layout(height=400)
        
        # Распределение по категориям
        all_categories = []
        for business in self.businesses_data:
            all_categories.extend(business['categories'])
        
        if all_categories:
            categories_count = pd.Series(all_categories).value_counts()
            
            fig4 = px.pie(
                values=categories_count.values,
                names=categories_count.index,
                title='Распределение предприятий по категориям'
            )
            fig4.update_layout(height=500)
        
        # Конвертируем в HTML
        chart1_html = pyo.plot(fig1, output_type='div', include_plotlyjs=False)
        chart2_html = pyo.plot(fig2, output_type='div', include_plotlyjs=False)
        
        charts_html = f"""
        <div class="row">
            <div class="col-md-6">
                {chart1_html}
            </div>
            <div class="col-md-6">
                {chart2_html}
            </div>
        </div>
        """
        
        if prices:
            chart3_html = pyo.plot(fig3, output_type='div', include_plotlyjs=False)
            charts_html += f"""
            <div class="row">
                <div class="col-md-6">
                    {chart3_html}
                </div>
            """
        
        if all_categories:
            chart4_html = pyo.plot(fig4, output_type='div', include_plotlyjs=False)
            charts_html += f"""
                <div class="col-md-6">
                    {chart4_html}
                </div>
            </div>
            """
        
        return charts_html
    
    def create_businesses_table(self):
        """Создание HTML таблицы предприятий"""
        if not self.businesses_data:
            return "<p>Нет данных о предприятиях</p>"
        
        table_rows = ""
        for i, business in enumerate(self.businesses_data, 1):
            phones_str = ', '.join(business['phones'])
            categories_str = ', '.join(business['categories'])
            website_link = f'<a href="{business["website"]}" target="_blank">Сайт</a>' if business['website'] else 'Нет'
            yandex_link = f'<a href="{business["url"]}" target="_blank">Карты</a>' if business['url'] else 'Нет'
            
            table_rows += f"""
            <tr>
                <td>{i}</td>
                <td><strong>{business['name']}</strong></td>
                <td><span class="badge bg-warning">{business['rating']}</span></td>
                <td>{business['address']}</td>
                <td>{categories_str}</td>
                <td>{phones_str}</td>
                <td>{website_link}</td>
                <td>{yandex_link}</td>
                <td><span class="badge bg-primary">{business['products_count']}</span></td>
                <td>{business['min_price']:,} ₽</td>
                <td>{business['max_price']:,} ₽</td>
                <td><strong>{business['avg_price']:,} ₽</strong></td>
            </tr>
            """
        
        return f"""
        <div class="table-responsive">
            <table class="table table-striped table-hover" id="businessesTable">
                <thead class="table-dark">
                    <tr>
                        <th>#</th>
                        <th>Название</th>
                        <th>Рейтинг</th>
                        <th>Адрес</th>
                        <th>Категории</th>
                        <th>Телефоны</th>
                        <th>Сайт</th>
                        <th>Карты</th>
                        <th>Услуг</th>
                        <th>Мин. цена</th>
                        <th>Макс. цена</th>
                        <th>Сред. цена</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        """
    
    def create_products_accordion(self):
        """Создание аккордеона с товарами/услугами по предприятиям"""
        if not self.products_data:
            return "<p>Нет данных о товарах/услугах</p>"
        
        # Группируем по предприятиям
        businesses_products = {}
        for product in self.products_data:
            business_name = product['business_name']
            if business_name not in businesses_products:
                businesses_products[business_name] = []
            businesses_products[business_name].append(product)
        
        # Сортируем предприятия по количеству услуг (больше услуг = выше)
        sorted_businesses = sorted(businesses_products.items(), key=lambda x: len(x[1]), reverse=True)
        
        accordion_items = ""
        for idx, (business_name, products) in enumerate(sorted_businesses):
            business_id = f"business_{idx}"
            
            # Получаем информацию о предприятии для заголовка
            business_info = None
            for business in self.businesses_data:
                if business['name'] == business_name:
                    business_info = business
                    break
            
            # Определяем статистику по ценам
            prices = [p['price_num'] for p in products if p['price_num'] > 0]
            min_price = min(prices) if prices else 0
            max_price = max(prices) if prices else 0
            avg_price = round(sum(prices) / len(prices)) if prices else 0
            
            # Создаем заголовок с дополнительной информацией
            header_info = f"""
            <div class="d-flex justify-content-between align-items-center w-100">
                <div>
                    <strong>🏥 {business_name}</strong>
                    {f'<span class="badge bg-warning ms-2">{business_info["rating"]}</span>' if business_info and business_info["rating"] != "Нет рейтинга" else ''}
                </div>
                <div class="text-end">
                    <span class="badge bg-primary me-2">{len(products)} услуг</span>
                    {f'<span class="badge bg-success">{avg_price:,} ₽ сред.</span>' if avg_price > 0 else ''}
                </div>
            </div>
            """
            
            # Создаем таблицу товаров (показываем все, но с пагинацией через CSS)
            table_rows = ""
            for i, product in enumerate(products, 1):
                description = product['description'][:150] + '...' if len(product['description']) > 150 else product['description']
                
                # Определяем цвет ряда по цене
                price_class = ""
                if product['price_num'] > 0:
                    if product['price_num'] > avg_price * 1.5:
                        price_class = "table-danger"  # Дорого
                    elif product['price_num'] < avg_price * 0.5:
                        price_class = "table-success"  # Дешево
                
                table_rows += f"""
                <tr class="{price_class}">
                    <td>{i}</td>
                    <td><strong>{product['title']}</strong></td>
                    <td class="text-nowrap"><strong>{product['price']}</strong></td>
                    <td>{description}</td>
                </tr>
                """
            
            # Дополнительная информация о предприятии
            additional_info = ""
            if business_info:
                additional_info = f"""
                <div class="row mb-3">
                    <div class="col-md-6">
                        <small class="text-muted">
                            📍 {business_info.get('address', 'Адрес не указан')}<br>
                            📞 {', '.join(business_info.get('phones', ['Не указаны']))}<br>
                            {f'🌐 <a href="{business_info["website"]}" target="_blank">Сайт</a>' if business_info.get('website') else ''}
                        </small>
                    </div>
                    <div class="col-md-6 text-end">
                        <small class="text-muted">
                            💰 Цены: {min_price:,} - {max_price:,} ₽<br>
                            📊 Среднее: {avg_price:,} ₽<br>
                            🔗 <a href="{business_info['url']}" target="_blank">Яндекс Карты</a>
                        </small>
                    </div>
                </div>
                """
            
            accordion_items += f"""
            <div class="accordion-item">
                <h2 class="accordion-header" id="heading_{business_id}">
                    <button class="accordion-button {'collapsed' if idx > 0 else ''}" type="button" 
                            data-bs-toggle="collapse" data-bs-target="#collapse_{business_id}" 
                            aria-expanded="{'true' if idx == 0 else 'false'}" aria-controls="collapse_{business_id}">
                        {header_info}
                    </button>
                </h2>
                <div id="collapse_{business_id}" class="accordion-collapse collapse {'show' if idx == 0 else ''}" 
                     aria-labelledby="heading_{business_id}" data-bs-parent="#productsAccordion">
                    <div class="accordion-body">
                        {additional_info}
                        
                        <div class="table-responsive">
                            <table class="table table-sm table-hover">
                                <thead class="table-dark">
                                    <tr>
                                        <th width="5%">#</th>
                                        <th width="35%">Название услуги</th>
                                        <th width="15%">Цена</th>
                                        <th width="45%">Описание</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {table_rows}
                                </tbody>
                            </table>
                        </div>
                        
                        <div class="mt-3 text-center">
                            <small class="text-muted">
                                Всего услуг: {len(products)} • 
                                Цветовая схема: 🟢 дешево, 🔴 дорого
                            </small>
                        </div>
                    </div>
                </div>
            </div>
            """
        
        return f"""
        <div class="accordion" id="productsAccordion">
            {accordion_items}
        </div>
        """
    
    def generate_dashboard(self, output_file=None):
        """Генерация статического HTML дашборда"""
        if not self.load_all_data():
            print("❌ Нет данных для создания дашборда")
            return False
        
        # Определяем имя файла
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"dashboard_{timestamp}.html"
        
        # Создаем статистику
        total_businesses = len(self.businesses_data)
        total_products = len(self.products_data)
        avg_products = round(total_products / total_businesses) if total_businesses > 0 else 0
        
        prices = [p['price_num'] for p in self.products_data if p['price_num'] > 0]
        avg_price = round(sum(prices) / len(prices)) if prices else 0
        
        # Генерируем компоненты
        charts_html = self.create_statistics_charts()
        businesses_table = self.create_businesses_table()
        products_accordion = self.create_products_accordion()
        
        # Создаем полный HTML
        html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏥 Дашборд стоматологических клиник</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .stat-card {{ transition: transform 0.2s; }}
        .stat-card:hover {{ transform: translateY(-5px); }}
        .table th {{ position: sticky; top: 0; background: #343a40; }}
        .nav-pills .nav-link.active {{ background-color: #0d6efd; }}
        
        /* Аккордеон стили */
        .accordion-button:not(.collapsed) {{
            background-color: #e7f3ff;
            border-color: #0d6efd;
        }}
        .accordion-button:focus {{
            box-shadow: 0 0 0 0.25rem rgba(13, 110, 253, 0.25);
        }}
        .accordion-item {{
            border: 1px solid #dee2e6;
            margin-bottom: 0.5rem;
            border-radius: 0.375rem;
        }}
        .accordion-item:last-of-type {{
            border-bottom: 1px solid #dee2e6;
        }}
        
        /* Цветовое кодирование цен */
        .table-success {{
            background-color: rgba(25, 135, 84, 0.1);
        }}
        .table-danger {{
            background-color: rgba(220, 53, 69, 0.1);
        }}
        
        /* Hover эффекты для таблиц */
        .table-hover tbody tr:hover td {{
            background-color: rgba(13, 110, 253, 0.1);
        }}
        
        /* Бейджи */
        .badge {{
            font-size: 0.75em;
        }}
        
        /* Адаптивность */
        @media (max-width: 768px) {{
            .accordion-button {{
                padding: 0.75rem;
            }}
            .table-responsive {{
                font-size: 0.875rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container-fluid">
        <!-- Заголовок -->
        <div class="row mt-4">
            <div class="col-12 text-center">
                <h1 class="display-4">🏥 Дашборд стоматологических клиник</h1>
                <p class="lead text-muted">Результаты парсинга от {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
                <hr>
            </div>
        </div>
        
        <!-- Статистические карточки -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card text-center stat-card bg-primary text-white">
                    <div class="card-body">
                        <h2 class="card-title">{total_businesses}</h2>
                        <p class="card-text">Предприятий</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center stat-card bg-success text-white">
                    <div class="card-body">
                        <h2 class="card-title">{total_products}</h2>
                        <p class="card-text">Товаров/услуг</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center stat-card bg-warning text-white">
                    <div class="card-body">
                        <h2 class="card-title">{avg_products}</h2>
                        <p class="card-text">Среднее услуг</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center stat-card bg-info text-white">
                    <div class="card-body">
                        <h2 class="card-title">{avg_price:,} ₽</h2>
                        <p class="card-text">Средняя цена</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Навигация по вкладкам -->
        <ul class="nav nav-pills justify-content-center mb-4" id="dashboardTabs" role="tablist">
            <li class="nav-item" role="presentation">
                <button class="nav-link active" id="charts-tab" data-bs-toggle="pill" data-bs-target="#charts" 
                        type="button" role="tab">📊 Аналитика</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="businesses-tab" data-bs-toggle="pill" data-bs-target="#businesses" 
                        type="button" role="tab">🏥 Предприятия</button>
            </li>
            <li class="nav-item" role="presentation">
                <button class="nav-link" id="products-tab" data-bs-toggle="pill" data-bs-target="#products" 
                        type="button" role="tab">🛍️ Товары/услуги</button>
            </li>
        </ul>
        
        <!-- Контент вкладок -->
        <div class="tab-content" id="dashboardContent">
            <!-- Аналитика -->
            <div class="tab-pane fade show active" id="charts" role="tabpanel">
                <h3>📊 Аналитические графики</h3>
                {charts_html}
            </div>
            
            <!-- Предприятия -->
            <div class="tab-pane fade" id="businesses" role="tabpanel">
                <h3>🏥 Список предприятий</h3>
                <p class="text-muted">Найдено {total_businesses} предприятий</p>
                {businesses_table}
            </div>
            
            <!-- Товары/услуги -->
            <div class="tab-pane fade" id="products" role="tabpanel">
                <h3>🛍️ Товары и услуги по предприятиям</h3>
                <p class="text-muted">Всего {total_products} товаров/услуг от {total_businesses} предприятий</p>
                <div class="alert alert-info" role="alert">
                    💡 <strong>Совет:</strong> Кликните на предприятие чтобы развернуть список услуг. 
                    Цветовая схема: 🟢 дешевые услуги, 🔴 дорогие услуги
                </div>
                {products_accordion}
            </div>
        </div>
        
        <!-- Футер -->
        <div class="row mt-5">
            <div class="col-12 text-center">
                <hr>
                <p class="text-muted">
                    Дашборд сгенерирован автоматически • 
                    <a href="{SEARCH_URL}" target="_blank">Исходный поиск</a> • 
                    Данные актуальны на {datetime.now().strftime('%d.%m.%Y %H:%M')}
                </p>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Инициализация поиска по таблицам
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Дашборд загружен: {total_businesses} предприятий, {total_products} услуг');
        }});
    </script>
</body>
</html>
"""
        
        # Сохраняем файл
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ Дашборд сохранен: {output_file}")
            print(f"🌐 Откройте файл в браузере")
            print(f"📊 Статистика: {total_businesses} предприятий, {total_products} услуг")
            
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
            return False

def main():
    """Главная функция"""
    print("🚀 Генерация статического HTML дашборда...")
    
    generator = StaticDashboardGenerator()
    success = generator.generate_dashboard()
    
    if success:
        print("\n🎉 Дашборд готов!")
    else:
        print("\n❌ Ошибка создания дашборда")

if __name__ == "__main__":
    main()
