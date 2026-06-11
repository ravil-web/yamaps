#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Интегрированный парсер Ozon для работы с системой дашбордов
"""

import time
import os
import json
import pandas as pd
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from src.config import TARGET_BUSINESSES_COUNT

class OzonParserIntegrated:
    """Интегрированный парсер Ozon"""
    
    def __init__(self, target_count=None):
        self.driver = None
        self.wait = None
        self.products = []
        self.processed_urls = set()
        # Используем значение из конфигурации, если не указано явно
        self.target_count = target_count if target_count is not None else TARGET_BUSINESSES_COUNT
        self.search_url = None
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Создаем папки для результатов
        self.create_directories()
    
    def create_directories(self):
        """Создание папок для результатов"""
        directories = ['parsing_results', 'dashboard', 'output']
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def setup_driver(self):
        """Настройка браузера"""
        print("🚀 Настройка браузера...")
        
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        # Подавление системных ошибок Windows
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--log-level=3')
        options.add_argument('--disable-logging')
        options.add_argument('--disable-gpu-logging')
        
        # Настройки для обхода блокировок
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-extensions')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 30)
            
            # Убираем признаки автоматизации
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ Браузер настроен успешно")
            return True
        except Exception as e:
            print(f"❌ Ошибка настройки браузера: {e}")
            return False
    
    def close_driver(self):
        """Закрытие браузера"""
        if self.driver:
            self.driver.quit()
            print("🔒 Браузер закрыт")
    
    def parse_ozon_products(self, url, max_products=None):
        """
        Основной метод парсинга товаров Ozon
        :param url: URL для парсинга
        :param max_products: максимальное количество товаров
        :return: список товаров
        """
        if not self.setup_driver():
            return []
        
        self.search_url = url
        max_products = max_products or self.target_count
        
        try:
            print(f"🌐 Переход на страницу: {url}")
            self.driver.get(url)
            time.sleep(3)
            
            # Определяем тип страницы и парсим соответственно
            if '/seller/' in url:
                products = self.parse_seller_products(max_products)
            elif '/search/' in url or '/category/' in url:
                products = self.parse_search_results(max_products)
            else:
                print("⚠️ Неизвестный тип страницы, пробуем общий парсинг")
                products = self.parse_general_products(max_products)
            
            self.products = products
            print(f"🎉 Парсинг завершен! Найдено {len(products)} товаров")
            
            # Сохранение результатов
            self.save_results()
            
            return products
            
        except Exception as e:
            print(f"❌ Ошибка парсинга: {e}")
            return []
        finally:
            self.close_driver()
    
    def parse_seller_products(self, max_products):
        """Парсинг товаров продавца"""
        print("🛒 Парсинг товаров продавца...")
        
        products = []
        current_page = 1
        max_pages = 10
        
        while len(products) < max_products and current_page <= max_pages:
            print(f"📄 Обработка страницы {current_page}")
            
            # Прокрутка для загрузки товаров
            self.scroll_for_products()
            
            # Поиск карточек товаров
            product_cards = self.find_product_cards()
            
            if not product_cards:
                print("❌ Карточки товаров не найдены")
                break
            
            print(f"📦 Найдено {len(product_cards)} карточек товаров")
            
            # Извлечение данных из карточек
            for card in product_cards:
                if len(products) >= max_products:
                    break
                
                try:
                    product_data = self.extract_product_data(card)
                    if product_data and product_data.get('name'):
                        products.append(product_data)
                        print(f"  ✅ {len(products)}. {product_data['name'][:50]}...")
                except Exception as e:
                    print(f"  ❌ Ошибка извлечения данных: {e}")
                    continue
            
            # Переход на следующую страницу
            if not self.go_to_next_page():
                print("📄 Следующая страница не найдена")
                break
            
            current_page += 1
            time.sleep(random.uniform(2, 4))
        
        return products
    
    def parse_search_results(self, max_products):
        """Парсинг результатов поиска"""
        print("🔍 Парсинг результатов поиска...")
        
        products = []
        
        # Прокрутка для загрузки товаров
        self.scroll_for_products()
        
        # Поиск карточек товаров
        product_cards = self.find_product_cards()
        
        if not product_cards:
            print("❌ Карточки товаров не найдены")
            return products
        
        print(f"📦 Найдено {len(product_cards)} карточек товаров")
        
        # Извлечение данных из карточек
        for card in product_cards:
            if len(products) >= max_products:
                break
            
            try:
                product_data = self.extract_product_data(card)
                if product_data and product_data.get('name'):
                    products.append(product_data)
                    print(f"  ✅ {len(products)}. {product_data['name'][:50]}...")
            except Exception as e:
                print(f"  ❌ Ошибка извлечения данных: {e}")
                continue
        
        return products
    
    def parse_general_products(self, max_products):
        """Общий парсинг товаров"""
        print("🛍️ Общий парсинг товаров...")
        
        products = []
        
        # Прокрутка для загрузки товаров
        self.scroll_for_products()
        
        # Поиск карточек товаров
        product_cards = self.find_product_cards()
        
        if not product_cards:
            print("❌ Карточки товаров не найдены")
            return products
        
        print(f"📦 Найдено {len(product_cards)} карточек товаров")
        
        # Извлечение данных из карточек
        for card in product_cards:
            if len(products) >= max_products:
                break
            
            try:
                product_data = self.extract_product_data(card)
                if product_data and product_data.get('name'):
                    products.append(product_data)
                    print(f"  ✅ {len(products)}. {product_data['name'][:50]}...")
            except Exception as e:
                print(f"  ❌ Ошибка извлечения данных: {e}")
                continue
        
        return products
    
    def scroll_for_products(self):
        """Прокрутка страницы для загрузки товаров"""
        print("📜 Прокрутка страницы для загрузки товаров...")
        
        try:
            # Множественные стратегии прокрутки
            for i in range(5):
                # Прокрутка вниз
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(1)
                
                # Прокрутка до конца
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # Проверяем кнопки загрузки
                self.click_load_more_buttons()
            
            print("✅ Прокрутка завершена")
            
        except Exception as e:
            print(f"⚠️ Ошибка прокрутки: {e}")
    
    def click_load_more_buttons(self):
        """Клик по кнопкам загрузки"""
        try:
            button_selectors = [
                "//button[contains(text(), 'Показать')]",
                "//button[contains(text(), 'Еще')]",
                "//button[contains(@class, 'load-more')]",
                "//button[contains(@class, 'show-more')]",
                "//a[contains(text(), 'Показать')]",
                "//a[contains(@class, 'load-more')]"
            ]
            
            for selector in button_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(2)
                            return True
                except:
                    continue
            
            return False
        except:
            return False
    
    def find_product_cards(self):
        """Поиск карточек товаров"""
        selectors = [
            '[class*="tile-root"]',
            '[class*="product-card"]',
            '[class*="item-card"]',
            '[data-widget="searchResultsV2"] > div > div',
            '.tile-root',
            '.product-card',
            '[class*="tile"]',
            '[class*="card"]'
        ]
        
        for selector in selectors:
            try:
                cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if cards and len(cards) > 3:  # Если найдено достаточно карточек
                    print(f"📦 Найдено {len(cards)} карточек селектором: {selector}")
                    return cards
            except:
                continue
        
        return []
    
    def extract_product_data(self, card):
        """Извлечение данных о товаре из карточки"""
        product = {}
        
        try:
            # Название товара
            name_selectors = [
                'span[class*="tsBody500Medium"]',
                '[class*="bq02_4_0-a"] span',
                'a[href*="/product/"] span[class*="tsBody"]',
                'span[class*="tsBody"]',
                'a[href*="/product/"]'
            ]
            
            product['name'] = self.extract_text(card, name_selectors, 'Название не найдено')
            
            # Если название не найдено, пробуем извлечь из ссылки
            if product['name'] == 'Название не найдено':
                try:
                    link_element = card.find_element(By.CSS_SELECTOR, 'a[href*="/product/"]')
                    product['name'] = link_element.get_attribute('title') or link_element.text.strip() or 'Название не найдено'
                except:
                    pass
            
            # Цена
            price_selectors = [
                'span[class*="tsHeadline500Medium"]',
                'span[class*="tsHeadline"]',
                '[class*="c35_3_1-a1"][class*="tsHeadline"]',
                'span[class*="c35_3_1-a1"]',
                'span[class*="price"]'
            ]
            
            price_text = self.extract_text(card, price_selectors, 'Цена не указана')
            if price_text != 'Цена не указана':
                # Убираем символы и пробелы, оставляем только цифры
                product['price'] = ''.join(filter(str.isdigit, price_text))
            else:
                product['price'] = price_text
            
            # Рейтинг
            rating_selectors = [
                'span[style*="color: rgb(255, 165, 0)"]',
                'span[class*="tsBodyControl400Small"]',
                'span[class*="rating"]',
                'div[class*="rating"] span'
            ]
            
            product['rating'] = self.extract_text(card, rating_selectors, 'Нет рейтинга')
            
            # Отзывы
            reviews_selectors = [
                'span[class*="tsBodyControl400Small"]',
                'span[class*="reviews"]',
                'div[class*="reviews"] span'
            ]
            
            product['reviews'] = self.extract_text(card, reviews_selectors, 'Нет отзывов')
            
            # Ссылка на товар
            try:
                link_element = card.find_element(By.CSS_SELECTOR, 'a[href*="/product/"]')
                product['link'] = link_element.get_attribute('href')
            except:
                product['link'] = 'Ссылка не найдена'
            
            # Доставка
            delivery_selectors = [
                'span[class*="delivery"]',
                'div[class*="delivery"] span',
                'span[class*="tsBody"]'
            ]
            
            product['delivery'] = self.extract_text(card, delivery_selectors, 'Информация о доставке отсутствует')
            
            # Дополнительные поля для совместимости с дашбордом
            product['address'] = product.get('delivery', 'Информация о доставке отсутствует')
            product['phone'] = 'Не указан'
            product['website'] = product.get('link', 'Ссылка не найдена')
            product['working_hours'] = 'Не указаны'
            product['description'] = product.get('name', 'Название не найдено')
            
        except Exception as e:
            print(f"❌ Ошибка извлечения данных товара: {e}")
            return None
        
        return product
    
    def extract_text(self, element, selectors, default_text=''):
        """Извлечение текста по селекторам"""
        for selector in selectors:
            try:
                found_element = element.find_element(By.CSS_SELECTOR, selector)
                text = found_element.text.strip()
                if text:
                    return text
            except:
                continue
        
        return default_text
    
    def go_to_next_page(self):
        """Переход на следующую страницу"""
        try:
            # Ищем кнопку "Следующая страница"
            next_selectors = [
                'a[aria-label="Следующая страница"]',
                'a[aria-label="Next page"]',
                'a[class*="pagination"]',
                'a[class*="next"]',
                'button[class*="next"]'
            ]
            
            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button.is_enabled():
                        next_button.click()
                        time.sleep(3)
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            print(f"❌ Ошибка перехода на следующую страницу: {e}")
            return False
    
    def save_results(self):
        """Сохранение результатов в различных форматах"""
        if not self.products:
            print("❌ Нет результатов для сохранения")
            return
        
        try:
            # Создаем папку для сессии
            session_dir = f"parsing_results/session_{self.session_id}"
            if not os.path.exists(session_dir):
                os.makedirs(session_dir)
            
            # Сохраняем JSON
            json_file = f"{session_dir}/ozon_products.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.products, f, ensure_ascii=False, indent=2)
            
            # Сохраняем Excel
            excel_file = f"output/ozon_products_{self.session_id}.xlsx"
            df = pd.DataFrame(self.products)
            df.to_excel(excel_file, index=False, engine='openpyxl')
            
            # Создаем сводку
            summary_file = f"{session_dir}/summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"Парсинг Ozon - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"URL: {self.search_url}\n")
                f.write(f"Найдено товаров: {len(self.products)}\n")
                f.write(f"Целевое количество: {self.target_count}\n")
                f.write(f"Успешность: {(len(self.products) / self.target_count * 100):.1f}%\n")
            
            print(f"💾 Результаты сохранены:")
            print(f"  📄 JSON: {json_file}")
            print(f"  📊 Excel: {excel_file}")
            print(f"  📋 Сводка: {summary_file}")
            
        except Exception as e:
            print(f"❌ Ошибка сохранения результатов: {e}")
    
    def get_results_for_dashboard(self):
        """Получение результатов в формате для дашборда"""
        return {
            'products': self.products,
            'total_count': len(self.products),
            'target_count': self.target_count,
            'success_rate': (len(self.products) / self.target_count * 100) if self.target_count > 0 else 0,
            'session_id': self.session_id,
            'search_url': self.search_url,
            'platform': 'Ozon'
        }

def main():
    """Основная функция для тестирования"""
    print("🚀 Интегрированный парсер Ozon запущен")
    
    # Примеры URL для тестирования
    test_urls = [
        "https://www.ozon.ru/seller/example-seller-123456/",
        "https://www.ozon.ru/search/?text=книги",
        "https://www.ozon.ru/category/knigi-16500/"
    ]
    
    parser = OzonParserIntegrated(target_count=10)
    
    try:
        for url in test_urls:
            print(f"\n{'='*50}")
            print(f"Тестирование URL: {url}")
            print(f"{'='*50}")
            
            products = parser.parse_ozon_products(url, max_products=10)
            if products:
                print(f"✅ Найдено {len(products)} товаров")
            else:
                print(f"❌ Товары не найдены")
            
            time.sleep(5)  # Пауза между тестами
    
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
