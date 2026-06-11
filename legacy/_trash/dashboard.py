#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
from datetime import datetime
import glob
from config import *

class DashboardAnalyzer:
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
            return go.Figure()
            
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
            return go.Figure()
        
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
        
        return fig
    
    def create_categories_chart(self, data):
        """Создание графика категорий"""
        categories = self.get_top_categories(data, 15)
        
        if not categories:
            return go.Figure()
            
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
        
        return fig
    
    def create_parsing_timeline(self, data):
        """Создание временной шкалы парсинга"""
        if not data:
            return go.Figure()
            
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
        
        return fig
    
    def create_products_analysis(self, data):
        """Анализ товаров и услуг"""
        if not data:
            return go.Figure()
            
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
            return go.Figure()
            
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
        
        return fig
    
    def create_geographic_analysis(self, data):
        """Географический анализ"""
        if not data:
            return go.Figure()
            
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
            return go.Figure()
            
        city_counts = pd.Series(cities).value_counts()
        
        fig = px.pie(
            values=city_counts.values,
            names=city_counts.index,
            title="Распределение предприятий по городам"
        )
        
        fig.update_layout(height=500)
        
        return fig

def create_dashboard():
    """Создание дашборда"""
    analyzer = DashboardAnalyzer()
    
    # Загружаем данные
    data = analyzer.load_all_data()
    stats = analyzer.create_summary_stats(data)
    
    # Создаем приложение Dash
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    
    app.layout = dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("📊 Дашборд анализа парсинга Yandex Maps", 
                       className="text-center mb-4"),
                html.Hr()
            ])
        ]),
        
        # Статистические карточки
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{stats.get('total_businesses', 0)}", className="card-title"),
                        html.P("Всего предприятий", className="card-text")
                    ])
                ], color="primary", outline=True)
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{stats.get('avg_rating', 0):.1f}", className="card-title"),
                        html.P("Средний рейтинг", className="card-text")
                    ])
                ], color="success", outline=True)
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{stats.get('total_products', 0)}", className="card-title"),
                        html.P("Товаров/услуг", className="card-text")
                    ])
                ], color="info", outline=True)
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{stats.get('success_rate', 0):.1f}%", className="card-title"),
                        html.P("Успешность парсинга", className="card-text")
                    ])
                ], color="warning", outline=True)
            ], width=3)
        ], className="mb-4"),
        
        # Графики
        dbc.Row([
            dbc.Col([
                dcc.Graph(
                    id='rating-distribution',
                    figure=analyzer.create_rating_distribution(data)
                )
            ], width=6),
            dbc.Col([
                dcc.Graph(
                    id='categories-chart',
                    figure=analyzer.create_categories_chart(data)
                )
            ], width=6)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dcc.Graph(
                    id='parsing-timeline',
                    figure=analyzer.create_parsing_timeline(data)
                )
            ], width=6),
            dbc.Col([
                dcc.Graph(
                    id='geographic-analysis',
                    figure=analyzer.create_geographic_analysis(data)
                )
            ], width=6)
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                dcc.Graph(
                    id='products-analysis',
                    figure=analyzer.create_products_analysis(data)
                )
            ], width=12)
        ], className="mb-4"),
        
        # Таблица с данными
        dbc.Row([
            dbc.Col([
                html.H3("📋 Детальные данные"),
                html.Div(id='data-table')
            ])
        ])
        
    ], fluid=True)
    
    @app.callback(
        Output('data-table', 'children'),
        Input('rating-distribution', 'clickData')
    )
    def update_table(click_data):
        if not data:
            return "Нет данных для отображения"
        
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
        
        return dbc.Table.from_dataframe(
            df_table.head(20), 
            striped=True, 
            bordered=True, 
            hover=True,
            responsive=True
        )
    
    return app

def main():
    """Запуск дашборда"""
    print("🚀 Запуск дашборда анализа парсинга...")
    
    app = create_dashboard()
    
    print("✅ Дашборд создан!")
    print("🌐 Откройте браузер и перейдите по адресу: http://127.0.0.1:8050")
    print("📊 Дашборд будет автоматически обновляться при изменении данных")
    
    app.run(debug=True, host='127.0.0.1', port=8050)

if __name__ == "__main__":
    main()
