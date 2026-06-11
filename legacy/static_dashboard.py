#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import glob
from config import *

class StaticDashboardGenerator:
    def __init__(self):
        self.data_folder = FOLDER_STRUCTURE['base_folder']
        self.businesses_folder = f"{self.data_folder}/{FOLDER_STRUCTURE['businesses_subfolder']}"
        self.logs_folder = f"{self.data_folder}/{FOLDER_STRUCTURE['logs_subfolder']}"
        
    def load_all_data(self):
        """Загрузка всех данных из папок парсинга"""
        all_businesses = []
        
        # Ищем все папки с данными предприятий
        business_folders = glob.glob(f"{self.businesses_folder}/*/")
        
        for folder in business_folders:
            try:
                # Ищем JSON файлы в папке
                json_files = glob.glob(f"{folder}/*.json")
                for json_file in json_files:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        data['folder'] = os.path.basename(folder)
                        data['file'] = os.path.basename(json_file)
                        all_businesses.append(data)
            except Exception as e:
                print(f"Ошибка загрузки {folder}: {e}")
                
        return all_businesses
    
    def create_summary_stats(self, data):
        """Создание сводной статистики"""
        if not data:
            return {}
            
        df = pd.DataFrame(data)
        
        # Обработка рейтингов
        ratings = []
        for b in data:
            rating = b.get('rating')
            if rating is not None:
                try:
                    if isinstance(rating, str):
                        rating = float(rating.replace(',', '.').replace('⭐', '').strip())
                    else:
                        rating = float(rating)
                    ratings.append(rating)
                except (ValueError, TypeError):
                    continue
        
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        stats = {
            'total_businesses': len(data),
            'avg_rating': avg_rating,
            'total_products': sum(len(b.get('products_and_services', [])) for b in data),
            'total_reviews': sum(len(b.get('reviews', [])) for b in data),
            'total_phones': sum(len(b.get('phones', [])) for b in data),
            'categories': self.get_top_categories(data),
            'parsing_sessions': len(set(b.get('folder', '') for b in data)),
            'success_rate': self.calculate_success_rate(data)
        }
        
        return stats
    
    def get_top_categories(self, data, top_n=10):
        """Получение топ категорий"""
        categories = []
        for business in data:
            cats = business.get('categories', [])
            if isinstance(cats, str):
                cats = [cats]
            categories.extend(cats)
            
        if not categories:
            return []
            
        category_counts = pd.Series(categories).value_counts()
        return category_counts.head(top_n).to_dict()
    
    def calculate_success_rate(self, data):
        """Расчет процента успешного парсинга"""
        if not data:
            return 0
            
        successful = sum(1 for b in data if b.get('name') and b.get('address'))
        return (successful / len(data)) * 100
    
    def create_rating_distribution(self, data):
        """Создание графика распределения рейтингов"""
        if not data:
            return ""
            
        # Обработка рейтингов
        ratings = []
        for b in data:
            rating = b.get('rating')
            if rating is not None:
                try:
                    if isinstance(rating, str):
                        rating = float(rating.replace(',', '.').replace('⭐', '').strip())
                    else:
                        rating = float(rating)
                    ratings.append(rating)
                except (ValueError, TypeError):
                    continue
        
        if not ratings:
            return ""
        
        fig = px.histogram(
            x=ratings,
            nbins=20,
            title="Распределение рейтингов предприятий",
            labels={'x': 'Рейтинг', 'y': 'Количество предприятий'},
            color_discrete_sequence=['#1f77b4']
        )
        
        fig.update_layout(
            xaxis_title="Рейтинг",
            yaxis_title="Количество предприятий",
            showlegend=False
        )
        
        return fig.to_html(full_html=False, include_plotlyjs=False)
    
    def create_categories_chart(self, data):
        """Создание графика категорий"""
        categories = self.get_top_categories(data, 15)
        
        if not categories:
            return ""
            
        fig = px.bar(
            x=list(categories.values()),
            y=list(categories.keys()),
            orientation='h',
            title="Топ категорий предприятий",
            labels={'x': 'Количество', 'y': 'Категория'},
            color=list(categories.values()),
            color_continuous_scale='viridis'
        )
        
        fig.update_layout(
            xaxis_title="Количество предприятий",
            yaxis_title="Категория",
            height=600
        )
        
        return fig.to_html(full_html=False, include_plotlyjs=False)
    
    def create_parsing_timeline(self, data):
        """Создание временной шкалы парсинга"""
        if not data:
            return ""
            
        # Группируем по папкам (сессиям парсинга)
        sessions = {}
        for business in data:
            folder = business.get('folder', 'unknown')
            if folder not in sessions:
                sessions[folder] = []
            sessions[folder].append(business)
        
        # Создаем временную шкалу
        fig = go.Figure()
        
        for i, (session, businesses) in enumerate(sessions.items()):
            # Обработка рейтингов для сессии
            session_ratings = []
            session_names = []
            for b in businesses:
                rating = b.get('rating')
                if rating is not None:
                    try:
                        if isinstance(rating, str):
                            rating = float(rating.replace(',', '.').replace('⭐', '').strip())
                        else:
                            rating = float(rating)
                        session_ratings.append(rating)
                        session_names.append(b.get('name', 'Unknown'))
                    except (ValueError, TypeError):
                        continue
            
            if session_ratings:
                fig.add_trace(go.Scatter(
                    x=[i] * len(session_ratings),
                    y=session_ratings,
                    mode='markers',
                    name=f"Сессия {session}",
                    text=session_names,
                    hovertemplate='<b>%{text}</b><br>Рейтинг: %{y}<extra></extra>'
                ))
        
        fig.update_layout(
            title="Рейтинги предприятий по сессиям парсинга",
            xaxis_title="Сессия парсинга",
            yaxis_title="Рейтинг",
            height=400
        )
        
        return fig.to_html(full_html=False, include_plotlyjs=False)
    
    def create_geographic_analysis(self, data):
        """Географический анализ"""
        if not data:
            return ""
            
        # Извлекаем города из адресов
        cities = []
        for business in data:
            address = business.get('address', '')
            if address:
                # Простая логика извлечения города
                parts = address.split(',')
                if len(parts) > 1:
                    city = parts[-1].strip()
                    cities.append(city)
        
        if not cities:
            return ""
            
        city_counts = pd.Series(cities).value_counts()
        
        fig = px.pie(
            values=city_counts.values,
            names=city_counts.index,
            title="Распределение предприятий по городам"
        )
        
        fig.update_layout(height=500)
        
        return fig.to_html(full_html=False, include_plotlyjs=False)
    
    def create_products_analysis(self, data):
        """Анализ товаров и услуг"""
        if not data:
            return ""
            
        # Собираем все товары
        all_products = []
        for business in data:
            products = business.get('products_and_services', [])
            for product in products:
                if isinstance(product, dict):
                    all_products.append({
                        'name': product.get('name', 'Unknown'),
                        'price': product.get('price', 0),
                        'business': business.get('name', 'Unknown'),
                        'category': business.get('categories', ['Unknown'])[0] if business.get('categories') else 'Unknown'
                    })
        
        if not all_products:
            return ""
            
        df_products = pd.DataFrame(all_products)
        
        # График цен
        fig = px.box(
            df_products,
            x='category',
            y='price',
            title="Распределение цен по категориям",
            labels={'price': 'Цена (руб)', 'category': 'Категория'}
        )
        
        fig.update_layout(
            xaxis_title="Категория",
            yaxis_title="Цена (руб)",
            height=500
        )
        
        return fig.to_html(full_html=False, include_plotlyjs=False)
    
    def create_data_table(self, data):
        """Создание таблицы данных"""
        if not data:
            return ""
        
        df = pd.DataFrame(data)
        
        # Создаем таблицу с основными данными
        table_data = []
        for _, row in df.iterrows():
            table_data.append({
                'Название': row.get('name', 'N/A'),
                'Рейтинг': row.get('rating', 'N/A'),
                'Адрес': row.get('address', 'N/A')[:50] + '...' if len(str(row.get('address', ''))) > 50 else row.get('address', 'N/A'),
                'Телефоны': len(row.get('phones', [])),
                'Товары': len(row.get('products_and_services', [])),
                'Отзывы': len(row.get('reviews', [])),
                'Сессия': row.get('folder', 'N/A')
            })
        
        df_table = pd.DataFrame(table_data)
        
        # Создаем HTML таблицу
        html_table = df_table.head(20).to_html(
            classes=['table', 'table-striped', 'table-bordered', 'table-hover'],
            index=False,
            escape=False
        )
        
        return html_table
    
    def generate_html_dashboard(self):
        """Генерация статического HTML дашборда"""
        print("🚀 Генерация статического HTML дашборда...")
        
        # Загружаем данные
        data = self.load_all_data()
        stats = self.create_summary_stats(data)
        
        # Создаем графики
        rating_chart = self.create_rating_distribution(data)
        categories_chart = self.create_categories_chart(data)
        timeline_chart = self.create_parsing_timeline(data)
        geo_chart = self.create_geographic_analysis(data)
        products_chart = self.create_products_analysis(data)
        data_table = self.create_data_table(data)
        
        # Создаем HTML
        html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 Дашборд анализа парсинга Yandex Maps</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{
            background-color: #f8f9fa;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        .card {{
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border: none;
            border-radius: 10px;
        }}
        .card-title {{
            font-size: 2rem;
            font-weight: bold;
        }}
        .stats-card {{
            transition: transform 0.2s;
        }}
        .stats-card:hover {{
            transform: translateY(-5px);
        }}
        .chart-container {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .table {{
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 0;
            margin-bottom: 30px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1 class="text-center mb-0">📊 Дашборд анализа парсинга Yandex Maps</h1>
            <p class="text-center mb-0 mt-2">Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>

    <div class="container">
        <!-- Статистические карточки -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card stats-card text-white bg-primary">
                    <div class="card-body text-center">
                        <h4 class="card-title">{stats.get('total_businesses', 0)}</h4>
                        <p class="card-text">Всего предприятий</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stats-card text-white bg-success">
                    <div class="card-body text-center">
                        <h4 class="card-title">{stats.get('avg_rating', 0):.1f}</h4>
                        <p class="card-text">Средний рейтинг</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stats-card text-white bg-info">
                    <div class="card-body text-center">
                        <h4 class="card-title">{stats.get('total_products', 0)}</h4>
                        <p class="card-text">Товаров/услуг</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stats-card text-white bg-warning">
                    <div class="card-body text-center">
                        <h4 class="card-title">{stats.get('success_rate', 0):.1f}%</h4>
                        <p class="card-text">Успешность парсинга</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Графики -->
        <div class="row">
            <div class="col-md-6">
                <div class="chart-container">
                    {rating_chart}
                </div>
            </div>
            <div class="col-md-6">
                <div class="chart-container">
                    {categories_chart}
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="chart-container">
                    {timeline_chart}
                </div>
            </div>
            <div class="col-md-6">
                <div class="chart-container">
                    {geo_chart}
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-12">
                <div class="chart-container">
                    {products_chart}
                </div>
            </div>
        </div>

        <!-- Таблица данных -->
        <div class="row">
            <div class="col-12">
                <div class="chart-container">
                    <h3>📋 Детальные данные</h3>
                    {data_table}
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
        """
        
        # Сохраняем HTML файл
        output_file = f"{self.data_folder}/dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Дашборд сохранен: {output_file}")
        return output_file

def main():
    """Запуск генератора статического дашборда"""
    generator = StaticDashboardGenerator()
    output_file = generator.generate_html_dashboard()
    
    print(f"🌐 Откройте файл в браузере: {output_file}")
    print("📊 Дашборд содержит интерактивные графики и таблицы")

if __name__ == "__main__":
    main()
