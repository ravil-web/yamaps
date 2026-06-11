#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Генератор клиентского дашборда в стиле Bootstrap
Создает дашборд с навигацией по страницам и статистическими карточками
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

class ClientDashboardGenerator:
    """Генератор клиентского дашборда"""
    
    def __init__(self):
        self.javascript = self.get_javascript()
    
    def format_numbers(self, text):
        """Форматирует все числа в тексте для лучшей читаемости"""
        if not text or text == 'Цена не указана' or text == 'Нет оценок' or text == 'Не указано':
            return text
        
        # Извлекаем числа из текста
        import re
        numbers = re.findall(r'\d+', str(text))
        
        if not numbers:
            return text
        
        # Форматируем все найденные числа
        formatted_text = str(text)
        for number in numbers:
            formatted_number = f"{int(number):,}".replace(',', ' ')
            formatted_text = formatted_text.replace(number, formatted_number, 1)
        
        return formatted_text
    
    def format_price(self, price_text):
        """Форматирует цену для лучшей читаемости (совместимость)"""
        return self.format_numbers(price_text)
    
    def get_javascript(self):
        """Возвращает JavaScript код для дашборда"""
        return """
        <script>
            function showPage(pageId) {
                // Скрываем все страницы
                document.querySelectorAll('.page').forEach(page => {
                    page.classList.remove('active');
                });
                
                // Показываем выбранную страницу
                document.getElementById(pageId).classList.add('active');
            }
            
            function showBusinessProducts(businessName) {
                // Скрываем все страницы
                document.querySelectorAll('.page').forEach(page => {
                    page.classList.remove('active');
                });
                
                // Показываем страницу товаров
                document.getElementById('products-page').classList.add('active');
                
                // Прокручиваем к нужному предприятию
                const targetElement = document.querySelector(`[data-business="${businessName}"]`);
                if (targetElement) {
                    targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            }
            
            // Функция для работы с аккордеонами
            function toggleAccordion(button) {
                const target = button.getAttribute('data-target');
                const collapse = document.querySelector(target);
                
                if (!collapse) return;
                
                const isExpanded = button.getAttribute('aria-expanded') === 'true';
                
                if (isExpanded) {
                    // Закрываем
                    collapse.classList.remove('show');
                    button.classList.add('collapsed');
                    button.setAttribute('aria-expanded', 'false');
                } else {
                    // Открываем
                    collapse.classList.add('show');
                    button.classList.remove('collapsed');
                    button.setAttribute('aria-expanded', 'true');
                }
            }
            
            // Обработчики событий для аккордеонов
            document.addEventListener('DOMContentLoaded', function() {
                // Добавляем обработчики для всех кнопок аккордеонов
                document.querySelectorAll('.accordion-button').forEach(button => {
                    button.addEventListener('click', function(e) {
                        e.preventDefault();
                        toggleAccordion(this);
                    });
                });
                
                // Добавляем класс loading при загрузке страницы
                document.body.classList.add('loading');
                
                // Убираем класс loading через 1 секунду
                setTimeout(() => {
                    document.body.classList.remove('loading');
                }, 1000);
                
                // Добавляем эффекты при наведении на карточки
                document.querySelectorAll('.card').forEach(card => {
                    card.addEventListener('mouseenter', function() {
                        this.style.transform = 'translateY(-5px) scale(1.02)';
                    });
                    
                    card.addEventListener('mouseleave', function() {
                        this.style.transform = 'translateY(0) scale(1)';
                    });
                });
                
                // Добавляем эффекты при наведении на кнопки
                document.querySelectorAll('.btn').forEach(btn => {
                    btn.addEventListener('mouseenter', function() {
                        this.style.transform = 'translateY(-2px)';
                    });
                    
                    btn.addEventListener('mouseleave', function() {
                        this.style.transform = 'translateY(0)';
                    });
                });
            });
        </script>
        """
    
    def get_css_styles(self):
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 25%, #16213e 50%, #0f3460 75%, #533483 100%);
                margin: 0;
                padding: 0;
                min-height: 100vh;
                color: #ffffff;
                overflow-x: hidden;
            }
            
            body::before {
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: 
                    radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
                    radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
                    radial-gradient(circle at 40% 40%, rgba(120, 219, 255, 0.2) 0%, transparent 50%);
                pointer-events: none;
                z-index: -1;
            }
            
            .header {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(20px);
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
                color: white;
                padding: 30px 0;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
                position: relative;
                overflow: hidden;
            }
            
            .header::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
                animation: shimmer 3s infinite;
            }
            
            @keyframes shimmer {
                0% { left: -100%; }
                100% { left: 100%; }
            }
            
            .header h1 {
                font-size: 2.5rem;
                font-weight: 800;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                text-align: center;
                margin-bottom: 10px;
                text-shadow: 
                    0 0 30px rgba(102, 126, 234, 0.5),
                    -0.5px -0.5px 0 rgba(255, 255, 255, 0.6),
                    0.5px -0.5px 0 rgba(255, 255, 255, 0.6),
                    -0.5px 0.5px 0 rgba(255, 255, 255, 0.6),
                    0.5px 0.5px 0 rgba(255, 255, 255, 0.6);
            }
            
            .page {
                display: none;
                padding: 30px 0;
                animation: fadeIn 0.5s ease-in-out;
            }
            
            .page.active {
                display: block;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .back-btn {
                margin-bottom: 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border: none;
                color: white;
                padding: 15px 30px;
                border-radius: 50px;
                font-weight: 600;
                font-size: 1rem;
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
                position: relative;
                overflow: hidden;
            }
            
            .back-btn::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                transition: left 0.5s;
            }
            
            .back-btn:hover::before {
                left: 100%;
            }
            
            .back-btn:hover {
                transform: translateY(-3px) scale(1.05);
                box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
            }
            
            .chart-container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 
                    0 20px 40px rgba(0,0,0,0.3),
                    inset 0 1px 0 rgba(255,255,255,0.1);
                margin-bottom: 30px;
                position: relative;
                overflow: hidden;
                transition: all 0.3s ease;
            }
            
            .chart-container::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent);
            }
            
            .chart-container:hover {
                transform: translateY(-5px);
                box-shadow: 
                    0 25px 50px rgba(0,0,0,0.4),
                    inset 0 1px 0 rgba(255,255,255,0.2);
            }
            
            .card {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 20px;
                box-shadow: 
                    0 15px 35px rgba(0,0,0,0.2),
                    inset 0 1px 0 rgba(255,255,255,0.1);
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                position: relative;
                overflow: hidden;
            }
            
            .card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 2px;
                background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
                opacity: 0;
                transition: opacity 0.3s ease;
            }
            
            .card:hover::before {
                opacity: 1;
            }
            
            .card:hover {
                transform: translateY(-10px) scale(1.02);
                box-shadow: 
                    0 25px 50px rgba(0,0,0,0.3),
                    inset 0 1px 0 rgba(255,255,255,0.2);
            }
            
            .card-title {
                font-size: 2.5rem;
                font-weight: 800;
                background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                text-shadow: 0 0 20px rgba(255,255,255,0.3);
            }
            
            .stats-card {
                cursor: pointer;
                position: relative;
                overflow: hidden;
            }
            
            .stats-card::after {
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                width: 0;
                height: 0;
                background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
                transition: all 0.6s ease;
                transform: translate(-50%, -50%);
                border-radius: 50%;
            }
            
            .stats-card:hover::after {
                width: 300px;
                height: 300px;
            }
            
            .btn {
                border-radius: 50px;
                font-weight: 600;
                padding: 12px 24px;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
                border: none;
                white-space: nowrap;
            }
            
            .btn::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                transition: left 0.5s;
            }
            
            .btn:hover::before {
                left: 100%;
            }
            
            .btn-outline-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: 2px solid transparent;
                background-clip: padding-box;
            }
            
            .btn-outline-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
            }
            
            .btn-outline-info {
                background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
                color: white;
                border: 2px solid transparent;
            }
            
            .btn-outline-info:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 25px rgba(23, 162, 184, 0.4);
            }
            
            .btn-outline-success {
                background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                color: white;
                border: 2px solid transparent;
            }
            
            .btn-outline-success:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 25px rgba(40, 167, 69, 0.4);
            }
            
            .table {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 15px;
                overflow: hidden;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            
            .table thead th {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                font-weight: 600;
                border: none;
                padding: 20px 15px;
                text-transform: uppercase;
                letter-spacing: 1px;
                font-size: 0.9rem;
                text-align: left;
            }
            
            .table tbody tr {
                background: rgba(255, 255, 255, 0.05);
                transition: all 0.3s ease;
                border: none;
            }
            
            .table tbody tr:hover {
                background: rgba(255, 255, 255, 0.1);
                transform: scale(1.01);
            }
            
            .table tbody td {
                border: none;
                padding: 15px;
                color: #ffffff;
                vertical-align: middle;
            }
            
            .table tbody td.price-cell,
            .table thead th.price-cell {
                width: auto;
                min-width: 120px;
                white-space: nowrap;
                text-align: right;
            }
            
            .accordion {
                border-radius: 20px;
                overflow: hidden;
                box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            }
            
            .accordion-item {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                margin-bottom: 10px;
                border-radius: 15px;
                overflow: hidden;
                transition: all 0.3s ease;
            }
            
            .accordion-item:hover {
                background: rgba(255, 255, 255, 0.15);
                transform: translateY(-2px);
            }
            
            .accordion-button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                font-weight: 600;
                border: none;
                padding: 20px 25px;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            
            .accordion-button::after {
                background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='white'%3e%3cpath fill-rule='evenodd' d='M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z'/%3e%3c/svg%3e");
            }
            
            .accordion-button::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
                transition: left 0.5s;
            }
            
            .accordion-button:hover::before {
                left: 100%;
            }
            
            .accordion-button:not(.collapsed) {
                background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
                box-shadow: inset 0 -1px 0 rgba(255,255,255,0.1);
                color: white;
            }
            
            .accordion-button:not(.collapsed)::after {
                background-image: url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16' fill='white'%3e%3cpath fill-rule='evenodd' d='M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z'/%3e%3c/svg%3e");
            }
            
            .accordion-button:focus {
                box-shadow: 0 0 0 0.25rem rgba(102, 126, 234, 0.25);
            }
            
            .accordion-body {
                background: rgba(255, 255, 255, 0.05);
                color: #ffffff;
                padding: 25px;
            }
            
            .alert {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 15px;
                color: #ffffff;
                backdrop-filter: blur(20px);
            }
            
            .alert-info {
                background: linear-gradient(135deg, rgba(23, 162, 184, 0.2) 0%, rgba(19, 132, 150, 0.2) 100%);
                border-color: rgba(23, 162, 184, 0.3);
            }
            
            /* Анимации для загрузки */
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }
            
            .loading {
                animation: pulse 2s infinite;
            }
            
            /* Стили для мобильных устройств */
            @media (max-width: 768px) {
                .header h1 {
                    font-size: 2rem;
                }
                
                .chart-container {
                    padding: 20px;
                    margin-bottom: 20px;
                }
                
                .card-title {
                    font-size: 2rem;
                }
                
                .table tbody td.price-cell,
                .table thead th.price-cell {
                    min-width: 100px;
                    font-size: 0.9rem;
                }
            }
        </style>
        """
    
    def generate_businesses_table(self, businesses):
        """Генерация таблицы предприятий"""
        if not businesses:
            return '<p>Предприятия не найдены</p>'
        
        table_html = '''
        <table border="1" class="dataframe table table-striped table-bordered table-hover">
        <thead>
            <tr style="text-align: right;">
                <th>Название</th>
                <th>Рейтинг</th>
                <th>Адрес</th>
                <th>Телефоны</th>
                <th>Категории</th>
                <th>Товары/услуги</th>
                <th>Отзывы</th>
                <th>Ссылки</th>
            </tr>
        </thead>
        <tbody>
        '''
        
        for business in businesses:
            name = business.get('name', 'Не указано')
            rating = self.format_numbers(business.get('rating', 'Нет оценок'))
            
            # Исправляем отображение адреса
            address = business.get('address', '')
            
            # Очищаем адрес от лишних элементов
            if address:
                # Убираем лишние элементы из адреса
                address = address.replace('Маршрут', '').replace('Показать входы', '').replace('Маршру', '')
                address = address.replace('Маршру', '').replace('Показать', '').replace('входы', '')
                address = address.replace('  ', ' ').strip()  # Убираем двойные пробелы
                
                # Дополнительная очистка от лишних символов
                address = re.sub(r'[^\w\s,.-]', '', address)  # Оставляем только буквы, цифры, пробелы, запятые, точки, дефисы
                address = re.sub(r'\s+', ' ', address).strip()  # Убираем множественные пробелы
                
                # Если адрес стал пустым после очистки или слишком короткий
                if not address or len(address) < 3:
                    address = 'Не указан'
            else:
                # Пробуем получить адрес из разных источников
                working_hours = business.get('working_hours', {})
                if working_hours:
                    address = working_hours.get('current_status', '')
                    if address:
                        # Очищаем и этот адрес
                        address = address.replace('Маршрут', '').replace('Показать входы', '').replace('Маршру', '')
                        address = address.replace('  ', ' ').strip()
                    
                    if not address and working_hours.get('schedule'):
                        address = working_hours['schedule'][0] if working_hours['schedule'] else ''
                        if address:
                            address = address.replace('Маршрут', '').replace('Показать входы', '').replace('Маршру', '')
                            address = address.replace('  ', ' ').strip()
                
                if not address:
                    # Пробуем получить из URL
                    url = business.get('url', '')
                    if url and 'maps' in url:
                        address = 'Адрес в Яндекс.Картах'
                    else:
                        address = 'Не указан'
            
            # Создаем кликабельные ссылки для телефонов
            phone_list = business.get('phones', [])
            if phone_list:
                phone_links = []
                for phone in phone_list:
                    # Очищаем номер от лишних символов для tel: ссылки
                    clean_phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
                    phone_links.append(f'<a href="tel:{clean_phone}" class="btn btn-sm btn-outline-info"> {phone}</a>')
                phones = ' '.join(phone_links)
            else:
                phones = 'Не указаны'
            categories = ', '.join(business.get('categories', [])) if business.get('categories') else 'Не указаны'
            products_count = self.format_numbers(len(business.get('products', [])))
            reviews_count = business.get('reviews_count', '0')
            website = business.get('website', '') if business.get('website') else ''
            
            # Создаем кликабельную ссылку для сайта
            if website and website.startswith('http'):
                website_link = f'<a href="{website}" target="_blank" class="btn btn-sm btn-outline-primary">Сайт</a>'
            else:
                website_link = 'Не указан'
            
            # Создаем кликабельную ссылку для Яндекс.Карт
            yandex_url = business.get('url', '')
            if yandex_url and 'maps' in yandex_url:
                yandex_link = f'<a href="{yandex_url}" target="_blank" class="btn btn-sm btn-outline-success">🗺️ Карты</a>'
            else:
                yandex_link = 'Не указан'
            
            table_html += f'''
            <tr>
                <td>{name}</td>
                <td>{rating}</td>
                <td>{address}</td>
                <td>{phones}</td>
                <td>{categories}</td>
                <td>{products_count}</td>
                <td>{reviews_count}</td>
                <td>{website_link} {yandex_link}</td>
            </tr>
            '''
        
        table_html += '</tbody></table>'
        return table_html
    
    def generate_businesses_list(self, businesses):
        """Генерация компактного списка предприятий для главной страницы"""
        if not businesses:
            return '<p>Предприятия не найдены</p>'
        
        list_html = '''
        <div class="row">
        '''
        
        for business in businesses:
            name = business.get('name', 'Не указано')
            rating = self.format_numbers(business.get('rating', 'Нет оценок'))
            products_count = self.format_numbers(len(business.get('products', [])))
            
            # Создаем кликабельную ссылку для количества товаров конкретного предприятия
            business_name_escaped = name.replace("'", "\\'").replace('"', '\\"')
            products_link = f'<a href="#" onclick="showBusinessProducts(\'{business_name_escaped}\'); return false;" class="btn btn-sm btn-outline-primary">{products_count}</a>'
            
            # Создаем кликабельные ссылки для телефонов
            phone_list = business.get('phones', [])
            if phone_list:
                phone_links = []
                for phone in phone_list:
                    clean_phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
                    phone_links.append(f'<a href="tel:{clean_phone}" class="btn btn-sm btn-outline-info"> {phone}</a>')
                phones = ' '.join(phone_links)
            else:
                phones = 'Не указаны'
            
            # Создаем кликабельные ссылки для сайта и карт
            website = business.get('website', '')
            if website and website.startswith('http'):
                website_link = f'<a href="{website}" target="_blank" class="btn btn-sm btn-outline-primary">Сайт</a>'
            else:
                website_link = ''
            
            yandex_url = business.get('url', '')
            if yandex_url and 'maps' in yandex_url:
                yandex_link = f'<a href="{yandex_url}" target="_blank" class="btn btn-sm btn-outline-success">🗺️ Карты</a>'
            else:
                yandex_link = ''
            
            list_html += f'''
            <div class="col-md-6 col-lg-4 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <h5 class="card-title">{name}</h5>
                        <p class="card-text">
                            <strong>Рейтинг:</strong> {rating}<br>
                            <strong>Товаров/услуг:</strong> {products_link}<br>
                            <strong>Телефоны:</strong> {phones}
                        </p>
                        <div class="d-flex gap-2">
                            {website_link}
                            {yandex_link}
                        </div>
                    </div>
                </div>
            </div>
            '''
        
        list_html += '</div>'
        return list_html
    
    def generate_products_table(self, businesses):
        """Генерация аккордеона товаров по предприятиям с сравнением"""
        if not businesses:
            return '<p>Товары и услуги не найдены</p>'
        
        # Группируем товары для сравнения
        product_groups = defaultdict(list)
        for business in businesses:
            for product in business.get('products', []):
                product_name = product.get('name', '').lower().strip()
                if product_name:
                    product_groups[product_name].append({
                        'business': business.get('name', 'Неизвестно'),
                        'price': product.get('price', 'Цена не указана'),
                        'description': product.get('description', '')
                    })
        
        # Находим товары для сравнения (есть у нескольких предприятий)
        comparison_products = {name: offers for name, offers in product_groups.items() if len(offers) > 1}
        
        accordion_html = '''
        <div class="accordion" id="productsAccordion">
        '''
        
        # Сначала показываем сравнение товаров
        if comparison_products:
            accordion_html += f'''
            <div class="accordion-item" style="border: 2px solid #28a745; margin-bottom: 20px; border-radius: 15px;">
                <h2 class="accordion-header" id="heading-comparison">
                    <button class="accordion-button collapsed" type="button" data-target="#collapse-comparison" aria-expanded="false" aria-controls="collapse-comparison" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%);">
                        <strong>Сравнение товаров и услуг</strong> - {self.format_numbers(len(comparison_products))} групп для сравнения
                    </button>
                </h2>
                <div id="collapse-comparison" class="accordion-collapse collapse" aria-labelledby="heading-comparison">
                    <div class="accordion-body" style="background: rgba(40, 167, 69, 0.05);">
                        <div class="alert alert-success mb-3" style="background: linear-gradient(135deg, rgba(40, 167, 69, 0.2) 0%, rgba(32, 201, 151, 0.2) 100%); border: 1px solid rgba(40, 167, 69, 0.3);">
                            <strong>Товары и услуги, которые предлагают несколько предприятий:</strong>
                        </div>
            '''
            
            # Группируем товары по названиям для лучшего отображения
            for product_name, offers in comparison_products.items():
                accordion_html += f'''
                        <div class="card mb-4" style="border: 2px solid #28a745; background: rgba(255, 255, 255, 0.1); border-radius: 15px;">
                            <div class="card-header" style="background: linear-gradient(135deg, rgba(40, 167, 69, 0.2) 0%, rgba(32, 201, 151, 0.2) 100%); border-radius: 13px 13px 0 0;">
                                <h5 class="mb-0" style="color: #ffffff; font-weight: 700; text-shadow: 0 0 10px rgba(40, 167, 69, 0.5);">{product_name.title()}</h5>
                                <small style="color: rgba(255, 255, 255, 0.8);">{self.format_numbers(len(offers))} предложений</small>
                            </div>
                            <div class="card-body" style="background: rgba(40, 167, 69, 0.05);">
                '''
                
                for offer in offers:
                    accordion_html += f'''
                                <div class="row mb-3">
                                    <div class="col-12">
                                        <div class="p-3" style="background: rgba(255, 255, 255, 0.1); border-radius: 10px; border: 1px solid rgba(40, 167, 69, 0.3);">
                                            <div class="row align-items-center">
                                                <div class="col-md-8">
                                                    <h6 class="mb-1" style="color: #ffffff; font-weight: 600;">{offer['business']}</h6>
                                                    <p class="mb-0" style="color: rgba(255, 255, 255, 0.8); font-size: 0.9rem;">{offer['description']}</p>
                                                </div>
                                                <div class="col-md-4 text-end">
                                                    <span class="badge" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; font-size: 1rem; padding: 8px 16px;">{self.format_price(offer['price'])}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                    '''
                
                accordion_html += '''
                            </div>
                        </div>
                '''
            
            accordion_html += '''
                    </div>
                </div>
            </div>
            '''
        
        # Добавляем разделитель между сравнением и остальными товарами
        if comparison_products:
            accordion_html += '''
            <div class="text-center my-4">
                <hr style="border: 2px solid #667eea; border-radius: 2px;">
                <h4 style="color: #667eea; font-weight: 600;">Товары и услуги по предприятиям</h4>
                <hr style="border: 2px solid #667eea; border-radius: 2px;">
            </div>
            '''
        
        # Затем показываем товары по предприятиям
        for i, business in enumerate(businesses):
            business_name = business.get('name', 'Неизвестно')
            products = business.get('products', [])
            
            if not products:
                continue
            
            accordion_html += f'''
            <div class="accordion-item">
                <h2 class="accordion-header" id="heading{i}">
                    <button class="accordion-button collapsed" type="button" data-target="#collapse{i}" aria-expanded="false" aria-controls="collapse{i}">
                        <strong>{business_name}</strong> - {self.format_numbers(len(products))} товаров/услуг
                    </button>
                </h2>
                <div id="collapse{i}" class="accordion-collapse collapse" aria-labelledby="heading{i}">
                    <div class="accordion-body">
                        <div class="table-responsive">
                            <table class="table table-striped table-bordered table-hover">
                                <thead>
                                    <tr>
                                        <th>Название товара</th>
                                        <th class="price-cell">Цена</th>
                                        <th>Описание</th>
                                    </tr>
                                </thead>
                                <tbody>
            '''
            
            for product in products:
                name = product.get('name', 'Без названия')
                price = product.get('price', 'Цена не указана')
                description = product.get('description', '')
                
                accordion_html += f'''
                                    <tr>
                                        <td><strong>{name}</strong></td>
                                        <td class="price-cell">{self.format_price(price)}</td>
                                        <td>{description}</td>
                                    </tr>
                '''
            
            accordion_html += '''
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            '''
        
        accordion_html += '</div>'
        return accordion_html
    
    def generate_comparison_content(self, businesses):
        """Генерация контента для сравнения товаров с аккордеоном"""
        # Группируем товары по названиям
        product_groups = defaultdict(list)
        
        for business in businesses:
            for product in business.get('products', []):
                product_name = product.get('name', '').lower().strip()
                if product_name:
                    product_groups[product_name].append({
                        'business': business.get('name', 'Неизвестно'),
                        'price': product.get('price', 'Цена не указана'),
                        'description': product.get('description', '')
                    })
        
        # Фильтруем только группы для сравнения
        comparison_groups = {name: offers for name, offers in product_groups.items() if len(offers) > 1}
        
        if not comparison_groups:
            return '<div class="alert alert-info">Похожие услуги не найдены</div>'
        
        # Создаем аккордеон для каждой группы товаров
        accordion_html = '''
        <div class="accordion" id="comparisonAccordion">
        '''
        
        for i, (product_name, offers) in enumerate(comparison_groups.items()):
            accordion_html += f'''
            <div class="accordion-item">
                <h2 class="accordion-header" id="comparison-heading{i}">
                    <button class="accordion-button collapsed" type="button" data-target="#comparison-collapse{i}" aria-expanded="false" aria-controls="comparison-collapse{i}">
                        <strong>{product_name.title()}</strong> - {self.format_numbers(len(offers))} предложений
                    </button>
                </h2>
                <div id="comparison-collapse{i}" class="accordion-collapse collapse" aria-labelledby="comparison-heading{i}">
                    <div class="accordion-body">
                        <div class="table-responsive">
                            <table class="table table-striped table-bordered table-hover">
                                <thead>
                                    <tr>
                                        <th>Предприятие</th>
                                        <th class="price-cell">Цена</th>
                                        <th>Описание</th>
                                    </tr>
                                </thead>
                                <tbody>
            '''
            
            for offer in offers:
                accordion_html += f'''
                                    <tr>
                                        <td><strong>{offer['business']}</strong></td>
                                        <td class="price-cell">{self.format_price(offer['price'])}</td>
                                        <td>{offer['description']}</td>
                                    </tr>
                '''
            
            accordion_html += '''
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            '''
        
        accordion_html += '</div>'
        return accordion_html
    
    def generate_dashboard(self, json_file_path, output_dir=None, project_name=None):
        """Генерация полного HTML дашборда"""
        try:
            # Загружаем данные
            with open(json_file_path, 'r', encoding='utf-8') as f:
                businesses = json.load(f)
            
            if not businesses:
                print(" Нет данных для создания дашборда")
                return None
            
            # Определяем папку для сохранения (в корне проекта)
            if output_dir is None:
                output_dir = Path.cwd()  # Текущая папка проекта
            
            # Создаем папку dashboard в корне проекта
            dashboard_dir = output_dir / "dashboard"
            os.makedirs(dashboard_dir, exist_ok=True)
            
            # Статистика
            total_businesses = self.format_numbers(len(businesses))
            total_products = self.format_numbers(sum(len(b.get('products', [])) for b in businesses))
            # total_reviews = sum(int(b.get('reviews_count', 0)) for b in businesses if str(b.get('reviews_count', '')).isdigit())
            
            # Группируем товары для подсчета групп сравнения
            product_groups = defaultdict(list)
            for business in businesses:
                for product in business.get('products', []):
                    product_name = product.get('name', '').lower().strip()
                    if product_name:
                        product_groups[product_name].append(business.get('name', 'Неизвестно'))
            
            comparison_groups = self.format_numbers(len([group for group in product_groups.values() if len(group) > 1]))
            
            # Генерируем контент для страниц
            businesses_table = self.generate_businesses_table(businesses)
            products_table = self.generate_products_table(businesses)
            comparison_content = self.generate_comparison_content(businesses)
            
            # Полный HTML
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            html_content = f"""
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Аналитический дашборд стоматологических услуг</title>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
                {self.get_css_styles()}
            </head>
            <body>
                <div class="header">
                    <div class="container">
                        <h1 class="text-center mb-0">Аналитический дашборд стоматологических услуг</h1>
                        <p class="text-center mb-0 mt-2">Сгенерировано: {timestamp}</p>
                    </div>
                </div>

                <!-- Главная страница -->
                <div id="main-page" class="page active">
                    <div class="container">
                        <!-- Статистические карточки -->
                        <div class="row mb-4">
                            <div class="col-md-4">
                                <div class="card stats-card text-white" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);" onclick="showPage('businesses-page')">
                                    <div class="card-body text-center">
                                        <h4 class="card-title">{total_businesses}</h4>
                                        <p class="card-text">Предприятий</p>
                                        <small>Нажмите для просмотра списка</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card stats-card text-white" style="background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);" onclick="showPage('products-page')">
                                    <div class="card-body text-center">
                                        <h4 class="card-title">{total_products}</h4>
                                        <p class="card-text">Услуг всего</p>
                                        <small>Нажмите для просмотра по предприятиям</small>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <div class="card stats-card text-white" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%);" onclick="showPage('comparison-page')">
                                    <div class="card-body text-center">
                                        <h4 class="card-title">{comparison_groups}</h4>
                                        <p class="card-text">Групп для сравнения</p>
                                        <small>Нажмите для просмотра сравнения</small>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Список предприятий на главной странице -->
                        <div class="row mt-4">
                            <div class="col-12">
                                <h3 class="mb-3">Список предприятий</h3>
                                <div class="chart-container">
                                    {self.generate_businesses_list(businesses)}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Страница предприятий -->
                <div id="businesses-page" class="page">
                    <div class="container">
                        <button class="btn btn-secondary back-btn" onclick="showPage('main-page')">
Назад к главной странице
                        </button>
                        <h2>Список всех предприятий</h2>
                        <div class="chart-container">
                            {businesses_table}
                        </div>
                    </div>
                </div>

                <!-- Страница товаров -->
                <div id="products-page" class="page">
                    <div class="container">
                        <button class="btn btn-secondary back-btn" onclick="showPage('main-page')">
Назад к главной странице
                        </button>
                        <h2>Товары и услуги</h2>
                        <div class="chart-container">
                            {products_table}
                        </div>
                    </div>
                </div>

                <!-- Страница сравнения товаров -->
                <div id="comparison-page" class="page">
                    <div class="container">
                        <button class="btn btn-secondary back-btn" onclick="showPage('main-page')">
Назад к главной странице
                        </button>
                        <h2>🔄 Сравнение товаров и услуг</h2>
                        <div class="chart-container">
                            {comparison_content}
                        </div>
                    </div>
                </div>


                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
                {self.javascript}
            </body>
            </html>
            """
            
            # Сохраняем файл
            if project_name:
                base_name = project_name
            else:
                base_name = Path(json_file_path).stem
            output_file = os.path.join(dashboard_dir, f"client_dashboard_{base_name}.html")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"Клиентский дашборд создан: {output_file}")
            print(f"Статистика:")
            print(f"   Предприятий: {total_businesses}")
            print(f"   Товаров: {total_products}")
            print(f"   Групп для сравнения: {comparison_groups}")
            # print(f"   💬 Отзывов: {total_reviews}")
            
            return output_file
            
        except Exception as e:
            print(f"Ошибка создания дашборда: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    """Основная функция"""
    import glob
    
    # Ищем JSON файлы с результатами парсинга
    json_files = glob.glob("output/*.json")
    
    if not json_files:
        print("Не найдены JSON файлы с результатами парсинга")
        print("Запустите парсер сначала")
        return
    
    generator = ClientDashboardGenerator()
    
    for json_file in json_files:
        print(f"\nСоздание клиентского дашборда для: {json_file}")
        dashboard_file = generator.generate_dashboard(json_file)
        
        if dashboard_file:
            print(f"Откройте в браузере: {dashboard_file}")

if __name__ == "__main__":
    main()
