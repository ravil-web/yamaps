#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Универсальный парсер для Яндекс.Карт и Ozon
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
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

class UniversalParser:
    def __init__(self, headless=False, target_count=None):
        """
        Инициализация универсального парсера
        :param headless: True для работы без отображения браузера
        :param target_count: количество элементов для парсинга (0 = все найденные)
        """
        self.headless = headless
        self.target_count = target_count
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
    
    def setup_driver(self):
        """Настройка и запуск драйвера"""
        try:
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
            
            if self.headless:
                self.options.add_argument('--headless')
            
            # Дополнительные настройки для стабильности
            self.options.add_argument('--no-sandbox')
            self.options.add_argument('--disable-dev-shm-usage')
            self.options.add_argument('--disable-gpu')
            self.options.add_argument('--window-size=1920,1080')
            
            # Автоматическая установка ChromeDriver
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
    
    def detect_platform(self, url):
        """Определение платформы по URL"""
        if 'yandex.ru/maps' in url:
            return 'yandex_maps'
        elif 'ozon.ru' in url:
            return 'ozon'
        else:
            return 'unknown'
    
    def parse_yandex_maps(self, url):
        """Парсинг Яндекс.Карт"""
        print("🗺️ Запуск парсера Яндекс.Карт...")
        
        try:
            if not self.driver:
                if not self.setup_driver():
                    return False
            
            # Переход на страницу
            print(f"🌐 Переход на страницу: {url}")
            self.driver.get(url)
            time.sleep(3)
            
            # Поиск ссылок на предприятия
            print("🔍 Поиск ссылок на предприятия...")
            business_links = self.get_yandex_business_links()
            
            if not business_links:
                print("❌ Ссылки на предприятия не найдены")
                return False
            
            # Ограничиваем количество ссылок
            if self.target_count and self.target_count > 0:
                business_links = business_links[:self.target_count]
            
            print(f"📊 Найдено {len(business_links)} ссылок на предприятия")
            
            # Парсинг каждого предприятия
            businesses = []
            for i, link in enumerate(business_links, 1):
                print(f"🏢 Парсинг предприятия {i}/{len(business_links)}: {link}")
                
                try:
                    business_data = self.parse_yandex_business(link)
                    if business_data:
                        businesses.append(business_data)
                        print(f"✅ Предприятие {i} обработано")
                    else:
                        print(f"⚠️ Не удалось обработать предприятие {i}")
                    
                    # Задержка между запросами
                    time.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    print(f"❌ Ошибка при парсинге предприятия {i}: {e}")
                    continue
            
            self.results = businesses
            print(f"🎉 Парсинг завершен! Обработано {len(businesses)} предприятий")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка парсинга Яндекс.Карт: {e}")
            return False
    
    def parse_ozon(self, url):
        """Парсинг Ozon"""
        print("🛒 Запуск парсера Ozon...")
        
        try:
            if not self.driver:
                if not self.setup_driver():
                    return False
            
            # Переход на страницу
            print(f"🌐 Переход на страницу: {url}")
            self.driver.get(url)
            time.sleep(3)
            
            # Определяем тип страницы Ozon
            if '/seller/' in url:
                products = self.parse_ozon_seller(url)
            else:
                products = self.parse_ozon_products(url)
            
            if not products:
                print("❌ Товары не найдены")
                return False
            
            # Ограничиваем количество товаров
            if self.target_count and self.target_count > 0:
                products = products[:self.target_count]
            
            self.results = products
            print(f"🎉 Парсинг завершен! Найдено {len(products)} товаров")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка парсинга Ozon: {e}")
            return False
    
    def get_yandex_business_links(self):
        """Получение ссылок на предприятия в Яндекс.Картах"""
        try:
            # Прокрутка для загрузки контента
            self.scroll_yandex_page()
            
            # Поиск ссылок на предприятия
            selectors = [
                "//a[contains(@href, '/org/')]",
                "//a[contains(@class, 'search-snippet-view')]",
                "//a[contains(@class, 'business-snippet-view')]",
                "//a[contains(@class, 'orgpage-snippet-view')]"
            ]
            
            links = []
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        href = element.get_attribute('href')
                        if href and '/org/' in href and href not in links:
                            links.append(href)
                except:
                    continue
            
            return links[:50]  # Ограничиваем количество ссылок
            
        except Exception as e:
            print(f"❌ Ошибка получения ссылок: {e}")
            return []
    
    def scroll_yandex_page(self):
        """Прокрутка страницы Яндекс.Карт"""
        try:
            print("📜 Прокрутка страницы для загрузки контента...")
            
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
                "//button[contains(@class, 'show-more')]"
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
    
    def parse_yandex_business(self, url):
        """Парсинг отдельного предприятия Яндекс.Карт"""
        try:
            self.driver.get(url)
            time.sleep(2)
            
            business_data = {
                'name': '',
                'address': '',
                'phone': '',
                'website': '',
                'rating': '',
                'reviews_count': '',
                'working_hours': '',
                'description': '',
                'url': url
            }
            
            # Название
            try:
                name_element = self.driver.find_element(By.XPATH, "//h1[contains(@class, 'orgpage-header-view__header')]")
                business_data['name'] = name_element.text.strip()
            except:
                pass
            
            # Адрес
            try:
                address_element = self.driver.find_element(By.XPATH, "//span[contains(@class, 'orgpage-header-view__address')]")
                business_data['address'] = address_element.text.strip()
            except:
                pass
            
            # Телефон
            try:
                phone_element = self.driver.find_element(By.XPATH, "//a[contains(@href, 'tel:')]")
                business_data['phone'] = phone_element.text.strip()
            except:
                pass
            
            # Рейтинг
            try:
                rating_element = self.driver.find_element(By.XPATH, "//span[contains(@class, 'rating-view__rating')]")
                business_data['rating'] = rating_element.text.strip()
            except:
                pass
            
            return business_data
            
        except Exception as e:
            print(f"❌ Ошибка парсинга предприятия: {e}")
            return None
    
    def parse_ozon_seller(self, url):
        """Парсинг товаров продавца Ozon"""
        try:
            products = []
            current_page = 1
            max_pages = 5
            
            while current_page <= max_pages:
                print(f"📄 Обработка страницы {current_page}")
                
                # Прокрутка страницы
                self.scroll_ozon_page()
                
                # Поиск товаров
                product_cards = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'tile-root')]")
                
                if not product_cards:
                    print("❌ Товары не найдены")
                    break
                
                for card in product_cards:
                    try:
                        product_data = self.extract_ozon_product_data(card)
                        if product_data:
                            products.append(product_data)
                    except:
                        continue
                
                # Переход на следующую страницу
                if not self.go_to_next_page():
                    break
                
                current_page += 1
                time.sleep(2)
            
            return products
            
        except Exception as e:
            print(f"❌ Ошибка парсинга продавца Ozon: {e}")
            return []
    
    def parse_ozon_products(self, url):
        """Парсинг товаров Ozon по поисковому запросу"""
        try:
            products = []
            
            # Прокрутка страницы
            self.scroll_ozon_page()
            
            # Поиск товаров
            product_cards = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'tile-root')]")
            
            for card in product_cards:
                try:
                    product_data = self.extract_ozon_product_data(card)
                    if product_data:
                        products.append(product_data)
                except:
                    continue
            
            return products
            
        except Exception as e:
            print(f"❌ Ошибка парсинга товаров Ozon: {e}")
            return []
    
    def scroll_ozon_page(self):
        """Прокрутка страницы Ozon"""
        try:
            for i in range(3):
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(1)
                
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
        except:
            pass
    
    def extract_ozon_product_data(self, card):
        """Извлечение данных о товаре Ozon"""
        try:
            product_data = {
                'name': '',
                'price': '',
                'rating': '',
                'reviews': '',
                'link': '',
                'delivery': ''
            }
            
            # Название
            try:
                name_element = card.find_element(By.XPATH, ".//a[contains(@class, 'tile-hover-target')]")
                product_data['name'] = name_element.get_attribute('title') or name_element.text.strip()
                product_data['link'] = name_element.get_attribute('href')
            except:
                pass
            
            # Цена
            try:
                price_element = card.find_element(By.XPATH, ".//span[contains(@class, 'tsBody500Medium')]")
                product_data['price'] = price_element.text.strip()
            except:
                pass
            
            # Рейтинг
            try:
                rating_element = card.find_element(By.XPATH, ".//span[contains(@class, 'tsBodyControl400Small')]")
                product_data['rating'] = rating_element.text.strip()
            except:
                pass
            
            return product_data if product_data['name'] else None
            
        except:
            return None
    
    def go_to_next_page(self):
        """Переход на следующую страницу"""
        try:
            next_button = self.driver.find_element(By.XPATH, "//a[contains(@class, 'pagination-item') and contains(text(), '→')]")
            if next_button.is_enabled():
                next_button.click()
                time.sleep(3)
                return True
        except:
            pass
        return False
    
    def save_results(self):
        """Сохранение результатов"""
        try:
            if not self.results:
                print("❌ Нет результатов для сохранения")
                return False
            
            # Создаем папку для сессии
            session_dir = f"parsing_results/session_{self.session_id}"
            if not os.path.exists(session_dir):
                os.makedirs(session_dir)
            
            # Сохраняем JSON
            json_file = f"{session_dir}/results.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Результаты сохранены в {json_file}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка сохранения результатов: {e}")
            return False
    
    def parse(self, url):
        """Основной метод парсинга"""
        try:
            platform = self.detect_platform(url)
            print(f"🔍 Определена платформа: {platform}")
            
            if platform == 'yandex_maps':
                success = self.parse_yandex_maps(url)
            elif platform == 'ozon':
                success = self.parse_ozon(url)
            else:
                print(f"❌ Неподдерживаемая платформа: {platform}")
                return False
            
            if success:
                self.save_results()
                return True
            else:
                return False
                
        except Exception as e:
            print(f"❌ Ошибка парсинга: {e}")
            return False

def main():
    """Основная функция для тестирования"""
    print("🚀 Универсальный парсер запущен")
    
    # Примеры URL для тестирования
    test_urls = [
        "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/?ll=39.806284%2C47.275656&z=12",
        "https://www.ozon.ru/seller/example-seller-123456/"
    ]
    
    parser = UniversalParser(headless=False, target_count=10)
    
    try:
        for url in test_urls:
            print(f"\n{'='*50}")
            print(f"Тестирование URL: {url}")
            print(f"{'='*50}")
            
            success = parser.parse(url)
            if success:
                print(f"✅ Парсинг успешно завершен")
            else:
                print(f"❌ Парсинг завершился с ошибкой")
            
            time.sleep(5)  # Пауза между тестами
    
    finally:
        parser.close()

if __name__ == "__main__":
    main()
