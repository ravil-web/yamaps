#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Генератор HTML дашборда для результатов парсинга Яндекс.Карт
Создает интерактивный дашборд с аккордеоном предприятий и ссылками на товары
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

class HTMLDashboardGenerator:
    """Генератор HTML дашборда"""
    
    def __init__(self):
        self.css_styles = """
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
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }
        
        .header .stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        .content {
            padding: 30px;
        }
        
        .businesses-section {
            margin-bottom: 40px;
        }
        
        .section-title {
            font-size: 1.8em;
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #3498db;
        }
        
        .accordion {
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .accordion-item {
            border-bottom: 1px solid #ecf0f1;
        }
        
        .accordion-header {
            background: #f8f9fa;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .accordion-header:hover {
            background: #e9ecef;
        }
        
        .accordion-header.active {
            background: #3498db;
            color: white;
        }
        
        .business-name {
            font-size: 1.2em;
            font-weight: 600;
        }
        
        .business-meta {
            display: flex;
            gap: 20px;
            font-size: 0.9em;
            opacity: 0.8;
        }
        
        .accordion-icon {
            font-size: 1.5em;
            transition: transform 0.3s ease;
        }
        
        .accordion-header.active .accordion-icon {
            transform: rotate(180deg);
        }
        
        .accordion-content {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
            background: white;
        }
        
        .accordion-content.active {
            max-height: 1000px;
        }
        
        .business-details {
            padding: 25px;
            border-top: 1px solid #ecf0f1;
        }
        
        .business-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }
        
        .info-group {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }
        
        .info-title {
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 8px;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .info-content {
            color: #34495e;
            line-height: 1.5;
        }
        
        .products-section {
            margin-top: 20px;
        }
        
        .products-title {
            font-size: 1.3em;
            color: #2c3e50;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
        }
        
        .product-card {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 15px;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .product-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            border-color: #3498db;
        }
        
        .product-name {
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 8px;
        }
        
        .product-price {
            color: #27ae60;
            font-weight: 600;
            font-size: 1.1em;
        }
        
        .product-description {
            color: #7f8c8d;
            font-size: 0.9em;
            margin-top: 8px;
            line-height: 1.4;
        }
        
        .no-products {
            text-align: center;
            color: #95a5a6;
            font-style: italic;
            padding: 20px;
        }
        
        .footer {
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 20px;
            font-size: 0.9em;
        }
        
        .rating {
            display: inline-flex;
            align-items: center;
            gap: 5px;
        }
        
        .rating-stars {
            color: #f39c12;
        }
        
        .verified-badge {
            background: #27ae60;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin-left: 10px;
        }
        
        .social-links {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        
        .social-link {
            padding: 5px 10px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-size: 0.8em;
            transition: background 0.3s ease;
        }
        
        .social-link:hover {
            background: #2980b9;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2em;
            }
            
            .header .stats {
                flex-direction: column;
                gap: 15px;
            }
            
            .business-info {
                grid-template-columns: 1fr;
            }
            
            .products-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """
        
        self.javascript = """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Аккордеон функциональность
            const accordionHeaders = document.querySelectorAll('.accordion-header');
            
            accordionHeaders.forEach(header => {
                header.addEventListener('click', function() {
                    const content = this.nextElementSibling;
                    const isActive = this.classList.contains('active');
                    
                    // Закрываем все остальные
                    accordionHeaders.forEach(h => {
                        h.classList.remove('active');
                        h.nextElementSibling.classList.remove('active');
                    });
                    
                    // Открываем текущий если был закрыт
                    if (!isActive) {
                        this.classList.add('active');
                        content.classList.add('active');
                    }
                });
            });
            
            // Автоматически открываем первый элемент
            if (accordionHeaders.length > 0) {
                accordionHeaders[0].click();
            }
            
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
            
            document.querySelectorAll('.product-card').forEach(card => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                observer.observe(card);
            });
        });
        </script>
        """
    
    def generate_stars(self, rating):
        """Генерация звездочек для рейтинга"""
        if not rating or rating == 0:
            return "Нет оценок"
        
        full_stars = int(rating)
        has_half = rating % 1 >= 0.5
        
        stars = "★" * full_stars
        if has_half:
            stars += "☆"
        stars += "☆" * (5 - full_stars - (1 if has_half else 0))
        
        return f"{stars} ({rating})"
    
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
    
    def generate_business_html(self, business, index):
        """Генерация HTML для одного предприятия"""
        verified_badge = '<span class="verified-badge">✓ Верифицирован</span>' if business.get('verified') else ''
        
        # Социальные сети
        social_links = []
        social_data = business.get('social_links', {})
        if social_data.get('whatsapp'):
            social_links.append(f'<a href="{social_data["whatsapp"]}" class="social-link" target="_blank">WhatsApp</a>')
        if social_data.get('vk'):
            social_links.append(f'<a href="{social_data["vk"]}" class="social-link" target="_blank">VK</a>')
        if social_data.get('youtube'):
            social_links.append(f'<a href="{social_data["youtube"]}" class="social-link" target="_blank">YouTube</a>')
        
        social_html = '<div class="social-links">' + ''.join(social_links) + '</div>' if social_links else ''
        
        # Телефоны
        phones_html = '<br>'.join([f'<a href="tel:{phone}">{self.format_phone(phone)}</a>' for phone in business.get('phones', [])])
        
        # Услуги
        services_html = '<br>'.join(business.get('services', [])[:5])  # Первые 5 услуг
        
        # Товары
        products = business.get('products', [])
        products_html = ""
        
        if products:
            products_html = '<div class="products-grid">'
            for product in products[:12]:  # Максимум 12 товаров
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
        <div class="accordion-item">
            <div class="accordion-header">
                <div>
                    <div class="business-name">
                        {business.get('name', 'Без названия')}
                        {verified_badge}
                    </div>
                    <div class="business-meta">
                        <span class="rating">
                            <span class="rating-stars">{self.generate_stars(business.get('rating', 0))}</span>
                        </span>
                        <span>📞 {len(business.get('phones', []))} телефонов</span>
                        <span>🏷️ {len(business.get('categories', []))} категорий</span>
                        <span>🛍️ {len(products)} товаров</span>
                    </div>
                </div>
                <div class="accordion-icon">▼</div>
            </div>
            <div class="accordion-content">
                <div class="business-details">
                    <div class="business-info">
                        <div class="info-group">
                            <div class="info-title">📞 Контакты</div>
                            <div class="info-content">
                                {phones_html}
                                {social_html}
                            </div>
                        </div>
                        
                        <div class="info-group">
                            <div class="info-title">📍 Адрес</div>
                            <div class="info-content">
                                {business.get('address', 'Адрес не указан')}
                            </div>
                        </div>
                        
                        <div class="info-group">
                            <div class="info-title">🌐 Сайт</div>
                            <div class="info-content">
                                {f'<a href="{business.get("website")}" target="_blank">{business.get("website")}</a>' if business.get('website') else 'Сайт не указан'}
                            </div>
                        </div>
                        
                        <div class="info-group">
                            <div class="info-title">🏷️ Категории</div>
                            <div class="info-content">
                                {', '.join(business.get('categories', []))}
                            </div>
                        </div>
                        
                        <div class="info-group">
                            <div class="info-title">⭐ Рейтинг и отзывы</div>
                            <div class="info-content">
                                Рейтинг: {self.generate_stars(business.get('rating', 0))}<br>
                                Отзывов: {business.get('reviews_count', 0)}
                            </div>
                        </div>
                        
                        <div class="info-group">
                            <div class="info-title">🕒 Режим работы</div>
                            <div class="info-content">
                                Статус: {business.get('working_hours', {}).get('current_status', 'Не указан')}<br>
                                Часы: {business.get('working_hours', {}).get('schedule', 'Не указаны')}
                            </div>
                        </div>
                        
                        <div class="info-group">
                            <div class="info-title">🏆 Награды</div>
                            <div class="info-content">
                                {', '.join(business.get('awards', [])) if business.get('awards') else 'Наград нет'}
                            </div>
                        </div>
                        
                        <div class="info-group">
                            <div class="info-title">🔧 Услуги</div>
                            <div class="info-content">
                                {services_html}
                            </div>
                        </div>
                    </div>
                    
                    <div class="products-section">
                        <div class="products-title">
                            🛍️ Товары ({len(products)})
                        </div>
                        {products_html}
                    </div>
                </div>
            </div>
        </div>
        '''
    
    def generate_dashboard(self, json_file_path, output_dir="dashboards"):
        """Генерация полного HTML дашборда"""
        try:
            # Загружаем данные
            with open(json_file_path, 'r', encoding='utf-8') as f:
                businesses = json.load(f)
            
            if not businesses:
                print("❌ Нет данных для создания дашборда")
                return None
            
            # Создаем директорию
            os.makedirs(output_dir, exist_ok=True)
            
            # Статистика
            total_businesses = len(businesses)
            total_products = sum(len(b.get('products', [])) for b in businesses)
            verified_count = len([b for b in businesses if b.get('verified')])
            with_phones = len([b for b in businesses if b.get('phones')])
            
            # Генерируем HTML для предприятий
            businesses_html = ""
            for i, business in enumerate(businesses):
                businesses_html += self.generate_business_html(business, i)
            
            # Полный HTML
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M")
            html_content = f"""
            <!DOCTYPE html>
            <html lang="ru">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Дашборд парсинга Яндекс.Карт</title>
                {self.css_styles}
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📊 Дашборд парсинга Яндекс.Карт</h1>
                        <p>Результаты анализа предприятий и товаров</p>
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
                    
                    <div class="content">
                        <div class="businesses-section">
                            <h2 class="section-title">🏢 Предприятия</h2>
                            <div class="accordion">
                                {businesses_html}
                            </div>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>Дашборд создан: {timestamp} | Источник данных: {os.path.basename(json_file_path)}</p>
                    </div>
                </div>
                
                {self.javascript}
            </body>
            </html>
            """
            
            # Сохраняем файл
            base_name = Path(json_file_path).stem
            output_file = os.path.join(output_dir, f"dashboard_{base_name}.html")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ Дашборд создан: {output_file}")
            print(f"📊 Статистика:")
            print(f"   🏢 Предприятий: {total_businesses}")
            print(f"   🛍️ Товаров: {total_products}")
            print(f"   ✅ Верифицированных: {verified_count}")
            print(f"   📞 С телефонами: {with_phones}")
            
            return output_file
            
        except Exception as e:
            print(f"❌ Ошибка создания дашборда: {e}")
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
    
    generator = HTMLDashboardGenerator()
    
    for json_file in json_files:
        print(f"\n📊 Создание дашборда для: {json_file}")
        dashboard_file = generator.generate_dashboard(json_file)
        
        if dashboard_file:
            print(f"🌐 Откройте в браузере: {dashboard_file}")

if __name__ == "__main__":
    main()
