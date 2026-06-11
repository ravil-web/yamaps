#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Диагностика селекторов для извлечения данных
"""

import sys
import os
import time
from bs4 import BeautifulSoup

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from src.browser_manager import BrowserManager

def debug_selectors():
    """Диагностика селекторов на реальной странице"""
    print("🔍 Диагностика селекторов Яндекс Карт")
    print("=" * 50)
    
    # Создание конфигурации
    config = Config()
    config.HEADLESS = False
    
    # Создание менеджера браузера
    browser_manager = BrowserManager(config)
    
    try:
        # Инициализация браузера
        print("🚀 Инициализация браузера...")
        if not browser_manager.setup_driver():
            print("❌ Не удалось инициализировать браузер")
            return
        print("✅ Браузер инициализирован")
        
        # Переход на страницу
        test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/"
        print(f"📖 Переход на: {test_url}")
        
        if not browser_manager.navigate_to_url(test_url):
            print("❌ Не удалось перейти на страницу")
            return
        print("✅ Переход выполнен")
        
        # Ждем загрузки
        print("⏳ Ожидание загрузки страницы...")
        time.sleep(5)
        
        # Прокрутка
        print("📜 Прокрутка страницы...")
        browser_manager.scroll_page(max_scrolls=2)
        time.sleep(3)
        
        # Получение HTML
        print("📄 Получение HTML страницы...")
        html = browser_manager.get_page_source()
        
        # Сохранение HTML для анализа
        html_file = "debug_page.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"💾 HTML сохранен в: {html_file}")
        
        # Анализ с BeautifulSoup
        print("🔍 Анализ структуры страницы...")
        soup = BeautifulSoup(html, 'html.parser')
        
        # Поиск возможных контейнеров предприятий
        potential_selectors = [
            # Новые возможные селекторы
            'div[class*="search-snippet"]',
            'div[class*="business-snippet"]', 
            'div[class*="search-result"]',
            'div[class*="serp-item"]',
            'div[class*="card"]',
            'div[class*="item"]',
            'div[class*="company"]',
            'div[class*="organization"]',
            # Общие селекторы
            'article',
            'li[class*="item"]',
            'div[data-*]'
        ]
        
        print("\n📊 Анализ потенциальных селекторов:")
        print("-" * 50)
        
        for selector in potential_selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    print(f"✅ {selector}: найдено {len(elements)} элементов")
                    
                    # Показать первый элемент для анализа
                    if len(elements) > 0:
                        first_element = elements[0]
                        classes = first_element.get('class', [])
                        if classes:
                            print(f"   Классы: {', '.join(classes[:3])}")
                        
                        # Поиск текста внутри
                        text = first_element.get_text(strip=True)[:100]
                        if text:
                            print(f"   Текст: {text}...")
                        print()
                else:
                    print(f"❌ {selector}: не найдено")
            except Exception as e:
                print(f"❌ {selector}: ошибка - {e}")
        
        # Поиск конкретных текстовых паттернов
        print("\n🎯 Поиск специфичных паттернов:")
        print("-" * 50)
        
        # Поиск слов, характерных для стоматологии
        dental_keywords = ['стоматолог', 'зуб', 'клиника', 'врач', 'лечение', 'протез']
        
        for keyword in dental_keywords:
            elements = soup.find_all(text=lambda text: text and keyword.lower() in text.lower())
            if elements:
                print(f"🦷 '{keyword}': найдено {len(elements)} упоминаний")
                
                # Найти родительские элементы
                parents = set()
                for element in elements[:3]:  # Первые 3
                    parent = element.parent
                    if parent and parent.name != 'html':
                        parent_classes = parent.get('class', [])
                        if parent_classes:
                            parents.add(' '.join(parent_classes))
                
                if parents:
                    print(f"   Родительские классы: {list(parents)[:3]}")
        
        print("\n💡 Рекомендации:")
        print("1. Проверьте debug_page.html в браузере")
        print("2. Найдите структуру элементов предприятий")
        print("3. Обновите селекторы в data_extractor.py")
        
        # Пауза для ручного анализа
        print("\n👀 Браузер оставлен открытым для ручного анализа")
        print("Нажмите Enter для закрытия...")
        input()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("🔚 Закрытие браузера...")
        browser_manager.close()

if __name__ == "__main__":
    debug_selectors()
