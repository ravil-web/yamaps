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
import re
from difflib import SequenceMatcher
from collections import defaultdict
from src.config import *

class ClientDashboardGenerator:
    def __init__(self, session_folder=None):
        if session_folder:
            # Используем конкретную папку сессии
            self.data_folder = session_folder
            self.businesses_folder = f"{session_folder}/businesses"
        else:
            # Используем общую папку (для обратной совместимости)
            self.data_folder = FOLDER_STRUCTURE['base_folder']
            self.businesses_folder = f"{self.data_folder}/{FOLDER_STRUCTURE['businesses_subfolder']}"
        
    def load_all_data(self):
        """Загрузка всех данных из папок парсинга"""
        all_businesses = []
        
        print(f"📁 Поиск данных в: {self.businesses_folder}")
        business_folders = glob.glob(f"{self.businesses_folder}/*/")
        print(f"📊 Найдено папок предприятий: {len(business_folders)}")
        
        for folder in business_folders:
            try:
                json_files = glob.glob(f"{folder}/*.json")
                print(f"📄 В папке {os.path.basename(folder)} найдено JSON файлов: {len(json_files)}")
                
                for json_file in json_files:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        data['folder'] = os.path.basename(folder)
                        data['file'] = os.path.basename(json_file)
                        all_businesses.append(data)
            except Exception as e:
                print(f"❌ Ошибка загрузки {folder}: {e}")
        
        print(f"✅ Загружено данных о {len(all_businesses)} предприятиях")        
        return all_businesses
    
    def normalize_service_name(self, name):
        """Нормализация названия услуги для сравнения"""
        if not name:
            return ""
        
        # Приводим к нижнему регистру
        normalized = name.lower().strip()
        
        # Удаляем лишние пробелы и символы
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = re.sub(r'[^\w\s]', '', normalized, flags=re.UNICODE)
        
        # Удаляем стоп-слова и детали
        stop_words = ['челюсть', 'единица', 'зуб', 'категория', 'сложности', 'группа', 
                     'первичный', 'повторный', 'лабораторная', 'клиническая', 'одномоментная', 
                     'отсроченная', '1', '2', '3', '4', 'один', 'два', 'три', 'четыре']
        
        words = normalized.split()
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        
        return ' '.join(filtered_words)
    
    def calculate_similarity(self, name1, name2):
        """Вычисление схожести между двумя названиями услуг"""
        norm1 = self.normalize_service_name(name1)
        norm2 = self.normalize_service_name(name2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # Используем SequenceMatcher для расчета схожести
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        
        # Дополнительные проверки на ключевые слова
        words1 = set(norm1.split())
        words2 = set(norm2.split())
        
        if words1 and words2:
            # Проверка пересечения ключевых слов
            common_words = words1.intersection(words2)
            word_similarity = len(common_words) / max(len(words1), len(words2))
            
            # Комбинируем схожесть текста и слов
            combined_similarity = (similarity * 0.7) + (word_similarity * 0.3)
            return combined_similarity
        
        return similarity
    
    def group_similar_services(self, data, similarity_threshold=0.6):
        """Группировка похожих услуг"""
        all_services = []
        
        # Собираем все услуги с информацией о предприятии
        for business in data:
            business_name = business.get('name', 'Unknown')
            services = business.get('products_and_services', [])
            
            for service in services:
                service_name = service.get('title') or service.get('name', '')
                if service_name and service_name.lower() != 'unknown':
                    all_services.append({
                        'name': service_name,
                        'price': service.get('price', ''),
                        'business': business_name,
                        'business_rating': business.get('rating', ''),
                        'business_address': business.get('address', ''),
                        'normalized_name': self.normalize_service_name(service_name)
                    })
        
        # Группируем похожие услуги
        service_groups = []
        used_indices = set()
        
        for i, service1 in enumerate(all_services):
            if i in used_indices:
                continue
                
            group = {
                'base_name': service1['name'],
                'normalized_name': service1['normalized_name'],
                'services': [service1],
                'businesses_count': 1,
                'min_price': self.extract_price_number(service1['price']),
                'max_price': self.extract_price_number(service1['price'])
            }
            used_indices.add(i)
            
            for j, service2 in enumerate(all_services):
                if j in used_indices:
                    continue
                    
                similarity = self.calculate_similarity(service1['name'], service2['name'])
                
                if similarity >= similarity_threshold:
                    group['services'].append(service2)
                    used_indices.add(j)
                    
                    price = self.extract_price_number(service2['price'])
                    if price:
                        if group['min_price'] is None or price < group['min_price']:
                            group['min_price'] = price
                        if group['max_price'] is None or price > group['max_price']:
                            group['max_price'] = price
            
            # Добавляем группу только если в ней больше одной услуги (есть что сравнивать)
            if len(group['services']) > 1:
                group['businesses_count'] = len(set(s['business'] for s in group['services']))
                service_groups.append(group)
        
        # Сортируем группы по количеству предприятий (наиболее популярные услуги сначала)
        service_groups.sort(key=lambda x: x['businesses_count'], reverse=True)
        
        return service_groups
    
    def extract_price_number(self, price_str):
        """Извлечение числового значения цены"""
        if not price_str:
            return None
            
        # Удаляем все символы кроме цифр
        numbers = re.findall(r'\d+', str(price_str))
        if numbers:
            return int(numbers[0])
        return None
    
    def create_summary_stats(self, data):
        """Создание сводной статистики"""
        if not data:
            return {}
            
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
        
        # Подсчитываем реальные товары
        total_products = 0
        for business in data:
            products = business.get('products_and_services', [])
            for product in products:
                if isinstance(product, dict):
                    product_name = product.get('title', '') or product.get('name', '')
                    if product_name:
                        total_products += 1
        
        stats = {
            'total_businesses': len(data),
            'avg_rating': avg_rating,
            'total_products': total_products,
            'total_reviews': sum(len(b.get('reviews', [])) for b in data),
            'total_phones': sum(len(b.get('phones', [])) for b in data),
            'categories': self.get_top_categories(data),
            'parsing_sessions': len(set(b.get('folder', '') for b in data))
        }
        
        return stats
    
    def create_services_comparison_chart(self, service_groups, max_groups=10):
        """Создание графика сравнения услуг"""
        if not service_groups:
            return '<div class="alert alert-info">Похожие услуги не найдены</div>'
        
        # Берем топ групп для отображения
        top_groups = service_groups[:max_groups]
        
        html_content = '''
        <div class="row">
            <div class="col-12">
                <h4 class="mb-3">🔍 Сравнение похожих услуг по предприятиям</h4>
                <p class="text-muted mb-4">Услуги, которые предлагают несколько предприятий с возможностью сравнения цен</p>
            </div>
        </div>
        '''
        
        for i, group in enumerate(top_groups):
            # Создаем уникальный ID для каждой группы
            group_id = f"service_group_{i}"
            
            # Сортируем услуги в группе по цене
            services_with_prices = []
            services_without_prices = []
            
            for service in group['services']:
                price = self.extract_price_number(service['price'])
                if price:
                    services_with_prices.append((service, price))
                else:
                    services_without_prices.append((service, 0))
            
            # Сортируем по цене
            services_with_prices.sort(key=lambda x: x[1])
            all_services = services_with_prices + services_without_prices
            
            # Определяем диапазон цен
            price_range = ""
            if group['min_price'] and group['max_price']:
                if group['min_price'] == group['max_price']:
                    price_range = f"{group['min_price']:,} ₽"
                else:
                    price_range = f"{group['min_price']:,} - {group['max_price']:,} ₽"
            
            html_content += f'''
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card border-primary">
                        <div class="card-header bg-primary text-white">
                            <div class="row">
                                <div class="col-md-8">
                                    <h5 class="mb-0">
                                        <i class="fas fa-tooth"></i> {group['base_name'][:80]}
                                        {('...' if len(group['base_name']) > 80 else '')}
                                    </h5>
                                </div>
                                <div class="col-md-4 text-end">
                                    <span class="badge bg-light text-dark">
                                        {group['businesses_count']} предприятий
                                    </span>
                                    {('<span class="badge bg-success ms-1">' + price_range + '</span>' if price_range else '')}
                                </div>
                            </div>
                        </div>
                        <div class="card-body">
                            <div class="row">
                                <div class="col-12">
                                    <button class="btn btn-outline-primary btn-sm mb-3" type="button" 
                                            data-bs-toggle="collapse" data-bs-target="#{group_id}" 
                                            aria-expanded="false" aria-controls="{group_id}">
                                        <i class="fas fa-eye"></i> Показать сравнение цен ({len(all_services)} вариантов)
                                    </button>
                                </div>
                            </div>
                            <div class="collapse" id="{group_id}">
                                <div class="table-responsive">
                                    <table class="table table-hover">
                                        <thead class="table-light">
                                            <tr>
                                                <th>Предприятие</th>
                                                <th>Цена</th>
                                                <th>Рейтинг</th>
                                                <th>Адрес</th>
                                                <th>Точное название</th>
                                            </tr>
                                        </thead>
                                        <tbody>
            '''
            
            for service, price in all_services:
                price_display = f"{price:,} ₽" if price > 0 else "Не указана"
                price_class = ""
                
                # Выделяем лучшие предложения
                if price > 0 and group['min_price'] and price == group['min_price']:
                    price_class = "text-success fw-bold"  # Самая низкая цена
                elif price > 0 and group['max_price'] and price == group['max_price']:
                    price_class = "text-danger"  # Самая высокая цена
                
                rating = service.get('business_rating', 'Нет рейтинга')
                rating_display = f"⭐ {rating}" if rating and rating != 'Нет рейтинга' else rating
                
                html_content += f'''
                                            <tr>
                                                <td><strong>{service['business']}</strong></td>
                                                <td class="{price_class}">{price_display}</td>
                                                <td>{rating_display}</td>
                                                <td class="text-muted small">{service.get('business_address', 'Не указан')}</td>
                                                <td class="text-muted small">{service['name']}</td>
                                            </tr>
                '''
            
            html_content += '''
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            '''
        
        return html_content
    
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
    
    def create_rating_distribution(self, data):
        """Создание графика распределения рейтингов"""
        if not data:
            return ""
            
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
    
    def create_geographic_analysis(self, data):
        """Географический анализ"""
        if not data:
            return ""
            
        cities = []
        for business in data:
            address = business.get('address', '')
            if address:
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
            
        all_products = []
        for business in data:
            products = business.get('products_and_services', [])
            for product in products:
                if isinstance(product, dict):
                    product_name = product.get('title', '') or product.get('name', 'Unknown')
                    all_products.append({
                        'name': product_name,
                        'price': product.get('price', 0),
                        'business': business.get('name', 'Unknown'),
                        'category': business.get('categories', ['Unknown'])[0] if business.get('categories') else 'Unknown'
                    })
        
        if not all_products:
            return ""
            
        df_products = pd.DataFrame(all_products)
        
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
    
    def generate_businesses_page(self, data):
        """Генерация страницы со списком предприятий"""
        if not data:
            return ""
        
        df = pd.DataFrame(data)
        
        # Создаем таблицу с основными данными
        table_data = []
        for _, row in df.iterrows():
            table_data.append({
                'Название': row.get('name', 'N/A'),
                'Рейтинг': row.get('rating', 'N/A'),
                'Адрес': row.get('address', 'N/A'),
                'Телефоны': ', '.join(row.get('phones', [])),
                'Категории': ', '.join(row.get('categories', [])),
                'Товары/услуги': len(row.get('products_and_services', [])),
                'Отзывы': len(row.get('reviews', [])),
                'Веб-сайт': row.get('website', 'N/A')
            })
        
        df_table = pd.DataFrame(table_data)
        
        html_table = df_table.to_html(
            classes=['table', 'table-striped', 'table-bordered', 'table-hover'],
            index=False,
            escape=False
        )
        
        return html_table
    
    def generate_products_page(self, data):
        """Генерация страницы с товарами и услугами в аккордеоне"""
        if not data:
            return ""
        
        # Группируем товары по предприятиям
        business_products = {}
        for business in data:
            business_name = business.get('name', 'Unknown')
            products = business.get('products_and_services', [])
            
            if products:
                business_products[business_name] = {
                    'products': products,
                    'categories': business.get('categories', []),
                    'address': business.get('address', 'N/A'),
                    'phones': business.get('phones', [])
                }
        
        if not business_products:
            return "<p>Товары и услуги не найдены</p>"
        
        # Создаем HTML аккордеон
        accordion_html = '<div class="accordion" id="productsAccordion">'
        
        for i, (business_name, business_data) in enumerate(business_products.items()):
            products = business_data['products']
            categories = business_data['categories']
            address = business_data['address']
            phones = business_data['phones']
            
            # Создаем таблицу товаров для этого предприятия
            products_table_data = []
            for product in products:
                if isinstance(product, dict):
                    product_name = product.get('title', '') or product.get('name', '')
                    if product_name:
                        products_table_data.append({
                            'Название': product_name,
                            'Цена': product.get('price', 'N/A'),
                            'Описание': product.get('description', 'N/A')
                        })
            
            if products_table_data:
                df_products = pd.DataFrame(products_table_data)
                products_table = df_products.to_html(
                    classes=['table', 'table-sm', 'table-striped', 'table-bordered'],
                    index=False,
                    escape=False
                )
                
                accordion_html += f"""
                <div class="accordion-item">
                    <h2 class="accordion-header" id="heading{i}">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse{i}" aria-expanded="false" aria-controls="collapse{i}">
                            <div class="d-flex justify-content-between align-items-center w-100 me-3">
                                <span><strong>{business_name}</strong></span>
                                <span class="badge bg-primary">{len(products_table_data)} товаров</span>
                            </div>
                        </button>
                    </h2>
                    <div id="collapse{i}" class="accordion-collapse collapse" aria-labelledby="heading{i}" data-bs-parent="#productsAccordion">
                        <div class="accordion-body">
                            <div class="row mb-3">
                                <div class="col-md-6">
                                    <strong>Категории:</strong> {', '.join(categories) if categories else 'N/A'}
                                </div>
                                <div class="col-md-6">
                                    <strong>Адрес:</strong> {address}
                                </div>
                            </div>
                            <div class="row mb-3">
                                <div class="col-12">
                                    <strong>Телефоны:</strong> {', '.join(phones) if phones else 'N/A'}
                                </div>
                            </div>
                            <div class="table-responsive">
                                {products_table}
                            </div>
                        </div>
                    </div>
                </div>
                """
        
        accordion_html += '</div>'
        
        return accordion_html
    
    def generate_reviews_page(self, data):
        """Генерация страницы с отзывами"""
        if not data:
            return ""
        
        all_reviews = []
        for business in data:
            reviews = business.get('reviews', [])
            for review in reviews:
                if isinstance(review, dict):
                    all_reviews.append({
                        'Предприятие': business.get('name', 'Unknown'),
                        'Автор': review.get('author', 'Unknown'),
                        'Рейтинг': review.get('rating', 'N/A'),
                        'Текст отзыва': review.get('text', 'N/A'),
                        'Дата': review.get('date', 'N/A'),
                        'Адрес': business.get('address', 'N/A')
                    })
        
        if not all_reviews:
            return "<p>Отзывы не найдены</p>"
        
        df_reviews = pd.DataFrame(all_reviews)
        
        html_table = df_reviews.to_html(
            classes=['table', 'table-striped', 'table-bordered', 'table-hover'],
            index=False,
            escape=False
        )
        
        return html_table
    
    def generate_categories_page(self, data):
        """Генерация страницы с категориями"""
        categories = self.get_top_categories(data, 50)
        
        if not categories:
            return "<p>Категории не найдены</p>"
        
        # Группируем предприятия по категориям
        category_businesses = {}
        for business in data:
            cats = business.get('categories', [])
            if isinstance(cats, str):
                cats = [cats]
            for cat in cats:
                if cat not in category_businesses:
                    category_businesses[cat] = []
                category_businesses[cat].append(business.get('name', 'Unknown'))
        
        # Создаем HTML для каждой категории
        categories_html = ""
        for category, count in categories.items():
            businesses_list = category_businesses.get(category, [])
            businesses_html = "<ul>" + "".join([f"<li>{name}</li>" for name in businesses_list[:10]]) + "</ul>"
            if len(businesses_list) > 10:
                businesses_html += f"<p><em>... и еще {len(businesses_list) - 10} предприятий</em></p>"
            
            categories_html += f"""
            <div class="card mb-3">
                <div class="card-header">
                    <h5 class="mb-0">{category} ({count} предприятий)</h5>
                </div>
                <div class="card-body">
                    {businesses_html}
                </div>
            </div>
            """
        
        return categories_html
    
    def generate_html_dashboard(self):
        """Генерация клиентского HTML дашборда"""
        print("🚀 Генерация клиентского HTML дашборда...")
        
        # Загружаем данные
        data = self.load_all_data()
        stats = self.create_summary_stats(data)
        
        # Создаем только сравнение услуг (убираем лишние графики)
        print("🔍 Анализ похожих услуг...")
        service_groups = self.group_similar_services(data)
        services_comparison = self.create_services_comparison_chart(service_groups)
        print(f"✅ Найдено {len(service_groups)} групп похожих услуг")
        
        # Создаем страницы (только необходимые)
        businesses_page = self.generate_businesses_page(data)
        products_page = self.generate_products_page(data)
        
        # Создаем HTML
        html_content = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>💰 Сравнение цен на стоматологические услуги</title>
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
            transition: transform 0.2s;
        }}
        .card:hover {{
            transform: translateY(-5px);
        }}
        .card-title {{
            font-size: 2rem;
            font-weight: bold;
        }}
        .stats-card {{
            cursor: pointer;
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
        .page {{
            display: none;
        }}
        .page.active {{
            display: block;
        }}
        .nav-link {{
            color: #495057;
            font-weight: 500;
        }}
        .nav-link.active {{
            color: #007bff !important;
            font-weight: bold;
        }}
        .back-btn {{
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1 class="text-center mb-0">💰 Сравнение цен на стоматологические услуги</h1>
            <p class="text-center mb-0 mt-2">Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>

    <!-- Главная страница -->
    <div id="main-page" class="page active">
        <div class="container">
            <!-- Статистические карточки -->
            <div class="row mb-4">
                <div class="col-md-4">
                    <div class="card stats-card text-white bg-primary" onclick="showPage('businesses-page')">
                        <div class="card-body text-center">
                            <h4 class="card-title">{stats.get('total_businesses', 0)}</h4>
                            <p class="card-text">Предприятий</p>
                            <small>Нажмите для просмотра списка</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card stats-card text-white bg-info" onclick="showPage('products-page')">
                        <div class="card-body text-center">
                            <h4 class="card-title">{stats.get('total_products', 0)}</h4>
                            <p class="card-text">Услуг всего</p>
                            <small>Нажмите для просмотра по предприятиям</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card stats-card text-white bg-success">
                        <div class="card-body text-center">
                            <h4 class="card-title">{len(service_groups)}</h4>
                            <p class="card-text">Групп для сравнения</p>
                            <small>Похожие услуги у разных предприятий</small>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Основной контент: Сравнение услуг -->
            <div class="row mt-4">
                <div class="col-12">
                    <div class="chart-container">
                        {services_comparison}
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Страница предприятий -->
    <div id="businesses-page" class="page">
        <div class="container">
            <button class="btn btn-secondary back-btn" onclick="showPage('main-page')">
                ← Назад к главной странице
            </button>
            <h2>📋 Список всех предприятий</h2>
            <div class="chart-container">
                {businesses_page}
            </div>
        </div>
    </div>

    <!-- Страница товаров -->
    <div id="products-page" class="page">
        <div class="container">
            <button class="btn btn-secondary back-btn" onclick="showPage('main-page')">
                ← Назад к главной странице
            </button>
            <h2>🛍️ Товары и услуги</h2>
            <div class="chart-container">
                {products_page}
            </div>
        </div>
    </div>



    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function showPage(pageId) {{
            // Скрываем все страницы
            document.querySelectorAll('.page').forEach(page => {{
                page.classList.remove('active');
            }});
            
            // Показываем выбранную страницу
            document.getElementById(pageId).classList.add('active');
        }}
    </script>
</body>
</html>
        """
        
        # Сохраняем HTML файл
        output_file = f"{self.data_folder}/client_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Клиентский дашборд сохранен: {output_file}")
        return output_file

def main():
    """Запуск генератора клиентского дашборда"""
    generator = ClientDashboardGenerator()
    output_file = generator.generate_html_dashboard()
    
    print(f"🌐 Откройте файл в браузере: {output_file}")
    print("📊 Дашборд содержит навигацию по страницам и интерактивные графики")

if __name__ == "__main__":
    main()
