#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Современный генератор HTML дашборда для результатов парсинга Яндекс.Карт
Создает интерактивный дашборд с группировкой товаров по предприятиям и сравнением
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

class ModernDashboardGenerator:
    """Современный генератор HTML дашборда"""
    
    def __init__(self):
        self.css_styles = """
        <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="0.5" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
            opacity: 0.3;
        }
        
        .header-content {
            position: relative;
            z-index: 1;
        }
        
        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            font-weight: 700;
            background: linear-gradient(45deg, #fff, #f0f8ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .header .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 30px;
            margin-top: 30px;
        }
        
        .stat-item {
            text-align: center;
            padding: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .stat-number {
            font-size: 2.5em;
            font-weight: 800;
            color: #4ade80;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
            font-weight: 500;
        }
        
        .content {
            padding: 40px;
        }
        
        .tabs {
            display: flex;
            background: #f8fafc;
            border-radius: 15px;
            padding: 5px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        
        .tab {
            flex: 1;
            padding: 15px 25px;
            text-align: center;
            cursor: pointer;
            border-radius: 10px;
            transition: all 0.3s ease;
            font-weight: 600;
            color: #64748b;
        }
        
        .tab.active {
            background: white;
            color: #1e293b;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .businesses-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 25px;
            margin-bottom: 40px;
        }
        
        .business-card {
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.08);
            border: 1px solid #e2e8f0;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .business-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        
        .business-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.12);
        }
        
        .business-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 20px;
        }
        
        .business-name {
            font-size: 1.4em;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 5px;
        }
        
        .business-meta {
            display: flex;
            gap: 15px;
            font-size: 0.9em;
            color: #64748b;
            margin-bottom: 15px;
        }
        
        .verified-badge {
            background: linear-gradient(45deg, #10b981, #059669);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }
        
        .rating {
            display: flex;
            align-items: center;
            gap: 5px;
            color: #f59e0b;
            font-weight: 600;
        }
        
        .business-info {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 25px;
        }
        
        .info-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9em;
            color: #64748b;
        }
        
        .info-item i {
            width: 16px;
            color: #667eea;
        }
        
        .products-section {
            margin-top: 25px;
        }
        
        .products-title {
            font-size: 1.2em;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .product-card {
            background: #f8fafc;
            border-radius: 12px;
            padding: 15px;
            border: 1px solid #e2e8f0;
            transition: all 0.3s ease;
        }
        
        .product-card:hover {
            background: white;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        
        .product-name {
            font-weight: 600;
            color: #1e293b;
            margin-bottom: 8px;
            font-size: 0.95em;
        }
        
        .product-price {
            color: #10b981;
            font-weight: 700;
            font-size: 1.1em;
            margin-bottom: 5px;
        }
        
        .product-description {
            color: #64748b;
            font-size: 0.85em;
            line-height: 1.4;
        }
        
        .comparison-section {
            background: #f8fafc;
            border-radius: 20px;
            padding: 30px;
            margin-top: 30px;
        }
        
        .comparison-title {
            font-size: 1.5em;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 20px;
            text-align: center;
        }
        
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.08);
        }
        
        .comparison-table th,
        .comparison-table td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }
        
        .comparison-table th {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            font-weight: 600;
        }
        
        .comparison-table tr:hover {
            background: #f8fafc;
        }
        
        .footer {
            background: #1e293b;
            color: white;
            text-align: center;
            padding: 30px;
            font-size: 0.9em;
        }
        
        .contact-links {
            display: flex;
            gap: 10px;
            margin-top: 10px;
            justify-content: center;
        }
        
        .contact-link {
            padding: 8px 16px;
            background: rgba(255,255,255,0.1);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-size: 0.85em;
            transition: all 0.3s ease;
        }
        
        .contact-link:hover {
            background: rgba(255,255,255,0.2);
            transform: translateY(-1px);
        }
        
        .no-products {
            text-align: center;
            color: #94a3b8;
            font-style: italic;
            padding: 30px;
            background: #f8fafc;
            border-radius: 12px;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2em;
            }
            
            .header .stats {
                grid-template-columns: repeat(2, 1fr);
                gap: 15px;
            }
            
            .businesses-grid {
                grid-template-columns: 1fr;
            }
            
            .business-info {
                grid-template-columns: 1fr;
            }
            
            .products-grid {
                grid-template-columns: 1fr;
            }
            
            .tabs {
                flex-direction: column;
            }
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        </style>
        """
        
        self.javascript = """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Переключение табов
            const tabs = document.querySelectorAll('.tab');
            const tabContents = document.querySelectorAll('.tab-content');
            
            tabs.forEach(tab => {
                tab.addEventListener('click', function() {
                    const target = this.getAttribute('data-target');
                    
                    // Убираем активный класс со всех табов и контента
                    tabs.forEach(t => t.classList.remove('active'));
                    tabContents.forEach(tc => tc.classList.remove('active'));
                    
                    // Добавляем активный класс к выбранному табу и контенту
                    this.classList.add('active');
                    document.getElementById(target).classList.add('active');
                });
            });
            
            // Анимация появления карточек
            const observerOptions = {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            };
            
            const observer = new IntersectionObserver(function(entries) {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.style.opacity = '1';
                        entry.target.style.transform = 'translateY(0)';
                    }
                });
            }, observerOptions);
            
            document.querySelectorAll('.business-card, .product-card').forEach(card => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                observer.observe(card);
            });
            
            // Плавная прокрутка к секциям
            document.querySelectorAll('a[href^="#"]').forEach(anchor => {
                anchor.addEventListener('click', function (e) {
                    e.preventDefault();
                    const target = document.querySelector(this.getAttribute('href'));
                    if (target) {
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                });
            });
        });
        </script>
        """
    
    def generate_stars(self, rating):
        """Генерация звездочек для рейтинга"""
        if not rating or rating == 0:
            return "Нет оценок"
        
        try:
            rating = float(rating)
            full_stars = int(rating)
            has_half = rating % 1 >= 0.5
            
            stars = "★" * full_stars
            if has_half:
                stars += "☆"
            stars += "☆" * (5 - full_stars - (1 if has_half else 0))
            
            return f"{stars} ({rating})"
        except:
            return "Нет оценок"
    
    def format_phone(self, phone):
        """Форматирование телефона"""
        if not phone:
            return "Не указан"
        
        # Убираем лишние символы
        phone = re.sub(r'[^\d+]', '', phone)
        
        # Форматируем российский номер
        if phone.startswith('+7') and len(phone) == 12:
            return f"+7 ({phone[2:5]}) {phone[5:8]}-{phone[8:10]}-{phone[10:12]}"
        elif phone.startswith('8') and len(phone) == 11:
            return f"+7 ({phone[1:4]}) {phone[4:7]}-{phone[7:9]}-{phone[9:11]}"
        
        return phone
    
    def generate_business_card(self, business, index):
        """Генерация карточки предприятия"""
        verified_badge = '<span class="verified-badge">✓ Верифицирован</span>' if business.get('verified') else ''
        
        # Контактные ссылки
        contact_links = []
        if business.get('phones'):
            contact_links.append(f'<a href="tel:{business["phones"][0]}" class="contact-link">📞 Позвонить</a>')
        if business.get('website'):
            contact_links.append(f'<a href="{business["website"]}" class="contact-link" target="_blank">🌐 Сайт</a>')
        if business.get('social_links', {}).get('whatsapp'):
            contact_links.append(f'<a href="{business["social_links"]["whatsapp"]}" class="contact-link" target="_blank">💬 WhatsApp</a>')
        
        contact_links_html = '<div class="contact-links">' + ''.join(contact_links) + '</div>' if contact_links else ''
        
        # Товары
        products = business.get('products', [])
        products_html = ""
        
        if products:
            products_html = '<div class="products-grid">'
            for product in products[:8]:  # Максимум 8 товаров на карточке
                price = product.get('price', 'Цена не указана')
                description = product.get('description', '')
                products_html += f'''
                <div class="product-card">
                    <div class="product-name">{product.get('name', 'Без названия')}</div>
                    <div class="product-price">{price}</div>
                    {f'<div class="product-description">{description}</div>' if description else ''}
                </div>
                '''
            products_html += '</div>'
        else:
            products_html = '<div class="no-products">Товары не найдены</div>'
        
        return f'''
        <div class="business-card">
            <div class="business-header">
                <div>
                    <div class="business-name">
                        {business.get('name', 'Без названия')}
                        {verified_badge}
                    </div>
                    <div class="business-meta">
                        <span class="rating">
                            <span>{self.generate_stars(business.get('rating', 0))}</span>
                        </span>
                        <span>📞 {len(business.get('phones', []))} телефонов</span>
                        <span>🏷️ {len(business.get('categories', []))} категорий</span>
                        <span>🛍️ {len(products)} товаров</span>
                    </div>
                </div>
            </div>
            
            <div class="business-info">
                <div class="info-item">
                    <i>📍</i>
                    <span>{business.get('address', 'Адрес не указан')}</span>
                </div>
                <div class="info-item">
                    <i>🕒</i>
                    <span>{business.get('working_hours', {}).get('current_status', 'Не указан')}</span>
                </div>
                <div class="info-item">
                    <i>🏷️</i>
                    <span>{', '.join(business.get('categories', [])[:2])}</span>
                </div>
                <div class="info-item">
                    <i>⭐</i>
                    <span>{business.get('reviews_count', 0)} отзывов</span>
                </div>
            </div>
            
            {contact_links_html}
            
            <div class="products-section">
                <div class="products-title">
                    🛍️ Товары ({len(products)})
                </div>
                {products_html}
            </div>
        </div>
        '''
    
    def generate_comparison_table(self, businesses):
        """Генерация таблицы сравнения товаров"""
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
        
        # Создаем таблицу сравнения
        table_html = '<table class="comparison-table">'
        table_html += '''
        <thead>
            <tr>
                <th>Товар</th>
                <th>Предприятие</th>
                <th>Цена</th>
                <th>Описание</th>
            </tr>
        </thead>
        <tbody>
        '''
        
        for product_name, offers in product_groups.items():
            if len(offers) > 1:  # Показываем только товары, которые есть у нескольких предприятий
                for i, offer in enumerate(offers):
                    row_class = 'highlight' if i == 0 else ''
                    table_html += f'''
                    <tr class="{row_class}">
                        <td><strong>{product_name.title()}</strong></td>
                        <td>{offer['business']}</td>
                        <td><span class="product-price">{offer['price']}</span></td>
                        <td>{offer['description']}</td>
                    </tr>
                    '''
                table_html += '<tr><td colspan="4" style="height: 10px; background: #f8fafc;"></td></tr>'
        
        table_html += '</tbody></table>'
        
        return table_html
    
    def generate_dashboard(self, json_file_path, output_dir=None):
        """Генерация полного HTML дашборда"""
        try:
            # Загружаем данные
            with open(json_file_path, 'r', encoding='utf-8') as f:
                businesses = json.load(f)
            
            if not businesses:
                print("❌ Нет данных для создания дашборда")
                return None
            
            # Определяем папку для сохранения
            if output_dir is None:
                # Создаем папку в той же директории, где находится JSON файл
                json_dir = Path(json_file_path).parent
                output_dir = json_dir
            
            # Создаем папку dashboard внутри папки с результатами парсинга
            dashboard_dir = output_dir / "dashboard"
            os.makedirs(dashboard_dir, exist_ok=True)
            
            # Статистика
            total_businesses = len(businesses)
            total_products = sum(len(b.get('products', [])) for b in businesses)
            verified_count = len([b for b in businesses if b.get('verified')])
            with_phones = len([b for b in businesses if b.get('phones')])
            
            # Генерируем карточки предприятий
            businesses_html = ""
            for i, business in enumerate(businesses):
                businesses_html += self.generate_business_card(business, i)
            
            # Генерируем таблицу сравнения
            comparison_html = self.generate_comparison_table(businesses)
            
            # Полный HTML
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
            html_content = f"""
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Современный дашборд парсинга Яндекс.Карт</title>
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
                {self.css_styles}
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="header-content">
                            <h1>📊 Современный дашборд</h1>
                            <p>Результаты анализа предприятий и товаров с Яндекс.Карт</p>
                            <div class="stats">
                                <div class="stat-item">
                                    <div class="stat-number">{total_businesses}</div>
                                    <div class="stat-label">Предприятий</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-number">{total_products}</div>
                                    <div class="stat-label">Товаров</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-number">{verified_count}</div>
                                    <div class="stat-label">Верифицированных</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-number">{with_phones}</div>
                                    <div class="stat-label">С телефонами</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="content">
                        <div class="tabs">
                            <div class="tab active" data-target="businesses-tab">🏢 Предприятия</div>
                            <div class="tab" data-target="comparison-tab">⚖️ Сравнение товаров</div>
                        </div>
                        
                        <div id="businesses-tab" class="tab-content active">
                            <div class="businesses-grid">
                                {businesses_html}
                            </div>
                        </div>
                        
                        <div id="comparison-tab" class="tab-content">
                            <div class="comparison-section">
                                <div class="comparison-title">⚖️ Сравнение товаров между предприятиями</div>
                                {comparison_html}
                            </div>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>Современный дашборд создан: {timestamp} | Источник данных: {os.path.basename(json_file_path)}</p>
                    </div>
                </div>
                
                {self.javascript}
            </body>
            </html>
            """
            
            # Сохраняем файл
            base_name = Path(json_file_path).stem
            output_file = os.path.join(dashboard_dir, f"modern_dashboard_{base_name}.html")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ Современный дашборд создан: {output_file}")
            print(f"📊 Статистика:")
            print(f"   🏢 Предприятий: {total_businesses}")
            print(f"   🛍️ Товаров: {total_products}")
            print(f"   ✅ Верифицированных: {verified_count}")
            print(f"   📞 С телефонами: {with_phones}")
            
            return output_file
            
        except Exception as e:
            print(f"❌ Ошибка создания дашборда: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    """Основная функция"""
    import glob
    
    # Ищем JSON файлы с результатами парсинга
    json_files = glob.glob("output/*.json")
    
    if not json_files:
        print("❌ Не найдены JSON файлы с результатами парсинга")
        print("Запустите парсер сначала")
        return
    
    generator = ModernDashboardGenerator()
    
    for json_file in json_files:
        print(f"\n📊 Создание современного дашборда для: {json_file}")
        dashboard_file = generator.generate_dashboard(json_file)
        
        if dashboard_file:
            print(f"🌐 Откройте в браузере: {dashboard_file}")

if __name__ == "__main__":
    main()
