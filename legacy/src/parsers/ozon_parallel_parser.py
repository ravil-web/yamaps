#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Параллельный парсер Ozon для получения таких же результатов
"""

import time
import json
import random
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

class OzonParallelParser:
    def __init__(self, headless=False):
        """
        Инициализация параллельного парсера Ozon
        :param headless: True для работы без отображения браузера
        """
        self.options = Options()
        
        # Настройки для имитации реального браузера
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Дополнительные настройки для обхода блокировок
        self.options.add_argument('--disable-web-security')
        self.options.add_argument('--allow-running-insecure-content')
        self.options.add_argument('--disable-features=VizDisplayCompositor')
        self.options.add_argument('--disable-extensions')
        
        if headless:
            self.options.add_argument('--headless')
        
        # Дополнительные настройки для стабильности
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--window-size=1920,1080')
        
        self.driver = None
        self.results = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Создаем папки для результатов
        self.create_directories()
        
    def create_directories(self):
        """Создание папок для результатов"""
        directories = ['parsing_results', 'dashboard', 'output']
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def start_driver(self):
        """Запуск драйвера"""
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.options)
            
            # Убираем признаки автоматизации
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ Драйвер успешно запущен")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка запуска драйвера: {e}")
            return False
    
    def close(self):
        """Закрытие драйвера"""
        if self.driver:
            self.driver.quit()
            print("🔒 Драйвер закрыт")
    
    def parse_seller_products(self, seller_url, max_products=200, max_pages=10):
        """
        Парсинг товаров продавца по URL
        :param seller_url: URL страницы продавца
        :param max_products: максимальное количество товаров для парсинга
        :param max_pages: максимальное количество страниц для парсинга
        :return: список словарей с информацией о товарах
        """
        if not self.driver:
            if not self.start_driver():
                return []
        
        products = []
        current_page = 1
        
        try:
            print(f"Переход на страницу продавца: {seller_url}")
            self.driver.get(seller_url)
            
            # Случайная задержка
            time.sleep(random.uniform(3, 6))
            
            while len(products) < max_products and current_page <= max_pages:
                print(f"Обработка страницы {current_page} (найдено товаров: {len(products)})")
                
                # Проверка на блокировку
                if self.check_for_blocking():
                    print("Пропуск страницы из-за блокировки")
                    break
                
                # Прокручиваем страницу для загрузки товаров
                self._scroll_page()
                
                # Ждем появления товаров
                wait = WebDriverWait(self.driver, 20)
                try:
                    # Пробуем найти товары разными способами
                    product_cards = self._find_product_cards_direct()
                    
                    if not product_cards:
                        print("Пробуем альтернативный способ поиска...")
                        product_cards = self._find_product_cards_alternative()
                    
                    if not product_cards:
                        print("Товары не найдены на странице")
                        break
                    
                    print(f"Найдено {len(product_cards)} карточек товаров")
                    
                    # Извлекаем данные из каждой карточки
                    for i, card in enumerate(product_cards):
                        if len(products) >= max_products:
                            break
                        
                        try:
                            product_data = self._extract_product_data(card)
                            if product_data and product_data.get('name') and product_data.get('name') != 'Название не найдено':
                                products.append(product_data)
                                print(f"  {len(products)}. {product_data.get('name', 'Без названия')[:50]}...")
                        except Exception as e:
                            print(f"Ошибка извлечения данных товара {i+1}: {e}")
                            continue
                    
                    # Переход на следующую страницу
                    if not self._go_to_next_page():
                        print("Следующая страница не найдена")
                        break
                    
                    current_page += 1
                    time.sleep(random.uniform(2, 4))
                    
                except TimeoutException:
                    print("Таймаут ожидания товаров")
                    break
                except Exception as e:
                    print(f"Ошибка обработки страницы: {e}")
                    break
            
            print(f"Парсинг завершен. Найдено {len(products)} товаров")
            return products
            
        except Exception as e:
            print(f"Ошибка парсинга продавца: {e}")
            return []
    
    def parse_products_with_details(self, seller_url, max_products=10, max_pages=2):
        """
        Парсинг товаров с детальной информацией
        :param seller_url: URL страницы продавца
        :param max_products: максимальное количество товаров для парсинга
        :param max_pages: максимальное количество страниц для парсинга
        :return: список словарей с детальной информацией о товарах
        """
        if not self.driver:
            if not self.start_driver():
                return []
        
        # Сначала получаем ссылки на товары
        product_links = self._get_product_links(seller_url, max_products, max_pages)
        
        if not product_links:
            print("Ссылки на товары не найдены")
            return []
        
        print(f"Найдено {len(product_links)} ссылок на товары")
        
        # Парсим детальную информацию по каждой ссылке
        detailed_products = []
        for i, link in enumerate(product_links[:max_products], 1):
            print(f"Парсинг товара {i}/{min(len(product_links), max_products)}: {link}")
            
            try:
                self.driver.get(link)
                time.sleep(random.uniform(2, 4))
                
                product_detail = self._extract_product_detail()
                if product_detail:
                    detailed_products.append(product_detail)
                    print(f"  ✅ {product_detail.get('name', 'Без названия')[:50]}...")
                else:
                    print(f"  ❌ Не удалось извлечь данные")
                
            except Exception as e:
                print(f"  ❌ Ошибка парсинга товара: {e}")
                continue
        
        print(f"Детальный парсинг завершен. Обработано {len(detailed_products)} товаров")
        return detailed_products
    
    def _get_product_links(self, seller_url, max_products=200, max_pages=10):
        """Получение ссылок на товары"""
        links = []
        current_page = 1
        
        try:
            self.driver.get(seller_url)
            time.sleep(random.uniform(3, 6))
            
            while len(links) < max_products and current_page <= max_pages:
                print(f"Получение ссылок со страницы {current_page}")
                
                self._scroll_page()
                
                # Ищем ссылки на товары
                link_selectors = [
                    'a[href*="/product/"]',
                    'a[href*="ozon.ru/product"]',
                    '[class*="tile-root"] a',
                    '[class*="product-card"] a'
                ]
                
                for selector in link_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            href = element.get_attribute('href')
                            if href and '/product/' in href and href not in links:
                                links.append(href)
                                if len(links) >= max_products:
                                    break
                    except:
                        continue
                
                if not self._go_to_next_page():
                    break
                
                current_page += 1
                time.sleep(random.uniform(2, 4))
            
            return links[:max_products]
            
        except Exception as e:
            print(f"Ошибка получения ссылок: {e}")
            return []
    
    def _find_product_cards_direct(self):
        """Поиск карточек товаров прямыми селекторами"""
        selectors = [
            '[class*="tile-root"]',
            '[class*="product-card"]',
            '[class*="item-card"]',
            '[data-widget="searchResultsV2"] > div > div',
            '.tile-root',
            '.product-card'
        ]
        
        for selector in selectors:
            try:
                cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if cards:
                    print(f"Найдено {len(cards)} карточек селектором: {selector}")
                    return cards
            except:
                continue
        
        return []
    
    def _find_product_cards_alternative(self):
        """Альтернативный поиск карточек товаров"""
        try:
            # Ищем по структуре страницы
            containers = self.driver.find_elements(By.CSS_SELECTOR, '[class*="container"], [class*="grid"], [class*="list"]')
            
            for container in containers:
                try:
                    cards = container.find_elements(By.CSS_SELECTOR, 'div[class*="tile"], div[class*="card"], div[class*="item"]')
                    if len(cards) > 5:  # Если найдено достаточно карточек
                        print(f"Найдено {len(cards)} карточек в контейнере")
                        return cards
                except:
                    continue
            
            return []
        except:
            return []
    
    def _extract_product_data(self, card):
        """
        Извлечение данных о товаре из карточки с актуальными селекторами
        :param card: элемент карточки товара
        :return: словарь с данными о товаре
        """
        product = {}
        
        try:
            # Название товара - актуальные селекторы
            name_selectors = [
                'span[class*="tsBody500Medium"]',
                '[class*="bq02_4_0-a"] span',
                'a[href*="/product/"] span[class*="tsBody"]',
                'span[class*="tsBody"]'
            ]
            
            product['name'] = self._extract_text(card, name_selectors, 'Название не найдено')
            
            # Если название не найдено, пробуем извлечь из ссылки
            if product['name'] == 'Название не найдено':
                try:
                    link_element = card.find_element(By.CSS_SELECTOR, 'a[href*="/product/"]')
                    product['name'] = link_element.get_attribute('title') or link_element.text.strip() or 'Название не найдено'
                except:
                    pass
            
            # Цена - актуальные селекторы
            price_selectors = [
                'span[class*="tsHeadline500Medium"]',
                'span[class*="tsHeadline"]',
                '[class*="c35_3_1-a1"][class*="tsHeadline"]',
                'span[class*="c35_3_1-a1"]'
            ]
            
            price_text = self._extract_text(card, price_selectors, 'Цена не указана')
            if price_text != 'Цена не указана':
                # Убираем символы и пробелы, оставляем только цифры
                product['price'] = ''.join(filter(str.isdigit, price_text))
            else:
                product['price'] = price_text
            
            # Рейтинг - актуальные селекторы
            rating_selectors = [
                'span[style*="color: rgb(255, 165, 0)"]',
                'span[class*="tsBodyControl400Small"]',
                'span[class*="rating"]',
                'div[class*="rating"] span'
            ]
            
            product['rating'] = self._extract_text(card, rating_selectors, 'Нет рейтинга')
            
            # Отзывы - актуальные селекторы
            reviews_selectors = [
                'span[class*="tsBodyControl400Small"]',
                'span[class*="reviews"]',
                'div[class*="reviews"] span'
            ]
            
            product['reviews'] = self._extract_text(card, reviews_selectors, 'Нет отзывов')
            
            # Ссылка на товар
            try:
                link_element = card.find_element(By.CSS_SELECTOR, 'a[href*="/product/"]')
                product['link'] = link_element.get_attribute('href')
            except:
                product['link'] = 'Ссылка не найдена'
            
            # Доставка - актуальные селекторы
            delivery_selectors = [
                'span[class*="delivery"]',
                'div[class*="delivery"] span',
                'span[class*="tsBody"]'
            ]
            
            product['delivery'] = self._extract_text(card, delivery_selectors, 'Информация о доставке отсутствует')
            
        except Exception as e:
            print(f"Ошибка извлечения данных товара: {e}")
            return None
        
        return product
    
    def _extract_product_detail(self):
        """
        Извлечение детальной информации о товаре со страницы карточки
        :return: словарь с детальной информацией о товаре
        """
        product = {}
        
        try:
            # Название товара - h1 с классом tsHeadline550Medium
            name_selectors = [
                'h1.tsHeadline550Medium',
                'h1.lm1_27',
                'h1[class*="tsHeadline"]',
                'h1[class*="lm1"]',
                'h1',
                '[class*="product-title"] h1'
            ]
            product['name'] = self._extract_text(self.driver, name_selectors, 'Название не найдено')
            
            # Цена - из блока с классами zk5_27 z3k_27
            price_selectors = [
                'span.zk5_27.z3k_27',
                'span[class*="zk5"]',
                'span[class*="z3k"]',
                'span[class*="price"]',
                '[class*="price"] span[class*="tsHeadline"]',
                'span[class*="tsHeadline"][class*="price"]',
                'span[class*="ll0"]'
            ]
            price_text = self._extract_text(self.driver, price_selectors, 'Цена не указана')
            if price_text != 'Цена не указана':
                # Извлекаем только цифры из цены
                price_digits = ''.join(filter(str.isdigit, price_text))
                product['price'] = price_digits if price_digits else price_text
            else:
                product['price'] = price_text
            
            # Рейтинг - из блока с классом ga5_3_1-a2
            rating_selectors = [
                'div.ga5_3_1-a2',
                'div[class*="ga5_3_1-a2"]',
                'div[class*="ga5_3_1"]',
                '[class*="rating"] span',
                '[class*="stars"] span',
                'span[class*="rating"]',
                'a[class*="ga5_3_1-a"] div[class*="ga5_3_1-a2"]'
            ]
            rating_text = self._extract_text(self.driver, rating_selectors, 'Нет рейтинга')
            product['rating'] = rating_text
            
            # Отзывы - из того же блока
            product['reviews'] = rating_text
            
            # Описание товара
            description_selectors = [
                'div[class*="description"]',
                'div[class*="product-description"]',
                'div[class*="kk6_27"]',
                'div[class*="k6k_27"]',
                'p[class*="description"]'
            ]
            product['description'] = self._extract_text(self.driver, description_selectors, 'Описание отсутствует')
            
            # Характеристики
            specifications_selectors = [
                'div[class*="specifications"]',
                'div[class*="characteristics"]',
                'div[class*="rl8_27"]',
                'div[class*="r4l_27"]'
            ]
            product['specifications'] = self._extract_text(self.driver, specifications_selectors, 'Характеристики отсутствуют')
            
            # Доставка
            delivery_selectors = [
                'div[class*="delivery"]',
                'div[class*="z7j_27"]',
                'span[class*="delivery"]'
            ]
            product['delivery'] = self._extract_text(self.driver, delivery_selectors, 'Информация о доставке отсутствует')
            
            # Продавец
            seller_selectors = [
                'a[href*="/seller/"]',
                'span[class*="seller"]',
                'div[class*="seller"]'
            ]
            product['seller'] = self._extract_text(self.driver, seller_selectors, 'Продавец не указан')
            
            # SKU из URL
            current_url = self.driver.current_url
            if '/product/' in current_url:
                try:
                    sku = current_url.split('/product/')[1].split('/')[0].split('-')[-1]
                    product['sku'] = sku
                except:
                    product['sku'] = 'SKU не найден'
            else:
                product['sku'] = 'SKU не найден'
            
            # URL товара
            product['url'] = current_url
            
        except Exception as e:
            print(f"Ошибка извлечения детальной информации: {e}")
            return None
        
        return product
    
    def _extract_text(self, element, selectors, default_text=''):
        """
        Извлечение текста по селекторам
        :param element: элемент для поиска
        :param selectors: список селекторов
        :param default_text: текст по умолчанию
        :return: извлеченный текст
        """
        for selector in selectors:
            try:
                if isinstance(element, webdriver.Chrome):
                    # Если элемент - это драйвер, ищем в документе
                    found_element = element.find_element(By.CSS_SELECTOR, selector)
                else:
                    # Если элемент - это конкретный элемент, ищем в нем
                    found_element = element.find_element(By.CSS_SELECTOR, selector)
                
                text = found_element.text.strip()
                if text:
                    return text
            except:
                continue
        
        return default_text
    
    def _scroll_page(self):
        """Прокрутка страницы для загрузки товаров"""
        try:
            # Прокручиваем страницу вниз
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Дополнительная прокрутка
            self.driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(1)
            
        except Exception as e:
            print(f"Ошибка прокрутки: {e}")
    
    def _go_to_next_page(self):
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
            print(f"Ошибка перехода на следующую страницу: {e}")
            return False
    
    def check_for_blocking(self):
        """Проверка на блокировку"""
        try:
            # Проверяем наличие капчи или блокировки
            blocking_indicators = [
                'captcha',
                'blocked',
                'access denied',
                'доступ запрещен'
            ]
            
            page_source = self.driver.page_source.lower()
            for indicator in blocking_indicators:
                if indicator in page_source:
                    return True
            
            return False
            
        except:
            return False
    
    def save_results(self, results, filename_prefix="ozon_products"):
        """Сохранение результатов"""
        try:
            if not results:
                print("Нет результатов для сохранения")
                return False
            
            # Создаем папку для сессии
            session_dir = f"parsing_results/session_{self.session_id}"
            if not os.path.exists(session_dir):
                os.makedirs(session_dir)
            
            # Сохраняем JSON
            json_file = f"{session_dir}/{filename_prefix}.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Результаты сохранены в {json_file}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения результатов: {e}")
            return False

def main():
    """Основная функция для тестирования"""
    print("🚀 Параллельный парсер Ozon запущен")
    
    # URL для тестирования
    test_url = "https://www.ozon.ru/seller/example-seller-123456/"
    
    parser = OzonParallelParser(headless=False)
    
    try:
        print(f"\n{'='*50}")
        print(f"Тестирование URL: {test_url}")
        print(f"{'='*50}")
        
        # Тест 1: Парсинг товаров продавца
        print("\n📦 Тест 1: Парсинг товаров продавца")
        products = parser.parse_seller_products(test_url, max_products=20, max_pages=3)
        
        if products:
            print(f"✅ Найдено {len(products)} товаров")
            parser.save_results(products, "seller_products")
            
            # Показываем примеры
            print("\n📋 Примеры найденных товаров:")
            for i, product in enumerate(products[:5], 1):
                print(f"  {i}. {product.get('name', 'Без названия')[:50]}...")
                print(f"     💰 Цена: {product.get('price', 'Не указана')}")
                print(f"     ⭐ Рейтинг: {product.get('rating', 'Не указан')}")
        else:
            print("❌ Товары не найдены")
        
        # Тест 2: Парсинг с детальной информацией
        print("\n📦 Тест 2: Парсинг с детальной информацией")
        detailed_products = parser.parse_products_with_details(test_url, max_products=5, max_pages=1)
        
        if detailed_products:
            print(f"✅ Найдено {len(detailed_products)} товаров с детальной информацией")
            parser.save_results(detailed_products, "seller_detailed_products")
            
            # Показываем примеры
            print("\n📋 Примеры детальной информации:")
            for i, product in enumerate(detailed_products[:3], 1):
                print(f"  {i}. {product.get('name', 'Без названия')[:50]}...")
                print(f"     💰 Цена: {product.get('price', 'Не указана')}")
                print(f"     📝 Описание: {product.get('description', 'Отсутствует')[:100]}...")
        else:
            print("❌ Детальная информация не найдена")
    
    finally:
        parser.close()

if __name__ == "__main__":
    main()
