#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
import os
import re
import csv
import logging
import signal
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement


class SingleBusinessParser:
    def __init__(self, session_folder=None):
        self.driver = None
        self.current_data = None
        self.business_url = None
        self.max_products = 10  # Лимит товаров по умолчанию
        self.session_folder = session_folder or "parsing_results/businesses"
        self.setup_logging()
        self.setup_signal_handlers()
    
    def setup_logging(self):
        # Проверяем, не настроен ли уже логгер
        if hasattr(self, 'logger') and self.logger.handlers:
            return
            
        os.makedirs("parsing_results/logs", exist_ok=True)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler = logging.FileHandler(f'parsing_results/logs/single_parser_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        self.logger = logging.getLogger('SingleBusinessParser')
        self.logger.setLevel(logging.DEBUG)
        
        # Очищаем существующие обработчики
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)  # Добавляем консольный обработчик
        self.logger.info("🚀 Система логирования инициализирована")
    
    def setup_signal_handlers(self):
        """Настройка обработчиков сигналов для сохранения данных при прерывании"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        self.logger.info("🛡️ Обработчики сигналов настроены")
    
    def signal_handler(self, signum, frame):
        """Обработчик сигналов прерывания"""
        self.logger.warning(f"⚠️ Получен сигнал прерывания {signum}")
        if self.current_data and self.business_url:
            self.logger.info("💾 Сохранение данных при прерывании...")
            try:
                self.save_business_data(self.business_url, self.current_data, interrupted=True)
                self.logger.info("✅ Данные сохранены при прерывании")
            except Exception as e:
                self.logger.error(f"❌ Ошибка сохранения при прерывании: {e}")
        
        if self.driver:
            self.driver.quit()
            self.logger.info("🔚 WebDriver закрыт при прерывании")
        
        sys.exit(0)
        
    def setup_driver(self):
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-logging')
        options.add_argument('--log-level=3')
        
        try:
            self.logger.info("🔧 Инициализация WebDriver...")
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(5)
            self.logger.info("✅ WebDriver инициализирован успешно")
            return True
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации WebDriver: {e}")
            return False
    
    def extract_basic_info(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {}
        try:
            self.logger.info("🔍 Извлечение базовой информации...")
            
            # Название
            name_selectors = [
                "//h1[@itemprop='name']",
                "//h1[contains(@class, 'orgpage-header-view__header')]", 
                "//h1[contains(@class, 'card-title-view__title')]",
                "//h1"
            ]
            data['name'] = self.extract_by_selectors(name_selectors)
            self.logger.info(f"   📝 Название: {data['name']}")
            
            # Рейтинг
            rating_elem = self.find_element_by_selectors([
                "//span[contains(@class, 'business-rating-badge-view__rating-text')]"
            ])
            data['rating'] = rating_elem.text.strip() if rating_elem else ""
            self.logger.info(f"   ⭐ Рейтинг: {data['rating']}")
            
            # Адрес - упрощенный поиск с таймаутом
            address_selectors = [
                "//div[contains(@class, 'orgpage-header-view__address')]",
                "//div[contains(@class, 'business-contacts-view__address')]",
                "//div[contains(@class, 'address')]",
                "//span[contains(@class, 'address')]",
                "//meta[@itemprop='address']/@content"
            ]
            
            data['address'] = ""
            try:
                # Быстрый поиск адреса с таймаутом 5 секунд
                address_elem = self.find_element_by_selectors_with_timeout(address_selectors, timeout=5)
                if address_elem:
                    if '/@' in address_selectors[0]:  # Для meta тегов
                        data['address'] = address_elem.get_attribute('content')
                    else:
                        data['address'] = address_elem.text.strip()
                        
                    # Очищаем адрес от кнопок
                    if data['address']:
                        lines = data['address'].split('\n')
                        clean_lines = []
                        for line in lines:
                            line = line.strip()
                            if (line and 
                                "Показать входы" not in line and 
                                "Маршрут" not in line and 
                                "Кнопка" not in line and
                                len(line) > 5):
                                clean_lines.append(line)
                        data['address'] = ' '.join(clean_lines)
                        
            except Exception as e:
                self.logger.warning(f"   ⚠️ Ошибка извлечения адреса: {e}")
                
            self.logger.info(f"   📍 Адрес: {data['address']}")
            
            # Категории
            categories = []
            category_selectors = [
                "//a[contains(@class, 'business-categories-view__category')]",
                "//div[contains(@class, 'business-card-title-view__categories')]//a",
                "//div[contains(@class, 'categories')]//a"
            ]
            
            for selector in category_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        text = elem.text.strip()
                        if text and text not in categories:
                            categories.append(text)
                except:
                    continue
            
            data['categories'] = categories
            self.logger.info(f"   🏷️ Категории: {categories}")
            
            return data
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения базовой информации: {e}")
            return {}
    
    def extract_contact_info(self) -> Dict[str, Any]:
        contacts: Dict[str, Any] = {}
        try:
            self.logger.info("📞 Извлечение контактной информации...")
            
            # Телефоны
            phones = []
            phone_selectors = [
                "//span[@itemprop='telephone']",
                "//div[contains(@class, 'card-phones-view__number')]//span"
            ]
            
            for selector in phone_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        phone = elem.text.strip()
                        if phone and phone not in phones:
                            phones.append(phone)
                except:
                    continue
            
            contacts['phones'] = phones
            self.logger.info(f"   📱 Телефоны: {phones}")
            
            # Сайт
            website_selectors = [
                "//a[contains(@class, 'business-urls-view__link')][@itemprop='url']"
            ]
            website_elem = self.find_element_by_selectors(website_selectors)
            contacts['website'] = website_elem.get_attribute('href') if website_elem else ""
            self.logger.info(f"   🌐 Сайт: {contacts['website']}")
            
            return contacts
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения контактов: {e}")
            return {}
    

    
    def extract_all_products_and_services(self) -> List[Dict[str, str]]:
        products: List[Dict[str, str]] = []
        try:
            self.logger.info("🛍️ Извлечение товаров и услуг...")
            
            # Ищем и переходим на вкладку товаров/услуг
            tab_found = False
            tab_selectors = [
                "//div[@class='tabs-select-view__title _name_prices']",
                "//div[contains(@class, 'tabs-select-view__title') and contains(text(), 'Цены')]",
                "//div[contains(@class, 'tabs-select-view__title') and contains(text(), 'Товары')]",
                "//div[contains(@class, 'tabs-select-view__title') and contains(text(), 'Услуги')]",
                "//div[contains(@class, 'tab') and contains(text(), 'Цены')]",
                "//div[contains(@class, 'tab') and contains(text(), 'Товары')]",
                "//div[contains(@class, 'tab') and contains(text(), 'Услуги')]",
                "//a[contains(@href, 'prices')]",
                "//a[contains(text(), 'Цены')]",
                "//a[contains(text(), 'Товары')]",
                "//a[contains(text(), 'Услуги')]"
            ]
            
            for selector in tab_selectors:
                try:
                    tab_elem = self.driver.find_element(By.XPATH, selector)
                    self.driver.execute_script("arguments[0].click();", tab_elem)
                    
                    # Ждем загрузки контента (оптимизация WebDriverWait)
                    try:
                        WebDriverWait(self.driver, 3).until(
                            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'business-full-items-grouped-view__item') or contains(@class, 'related-item-photo-view') or contains(@class, 'product-item')]"))
                        )
                    except TimeoutException:
                        time.sleep(1) # Fallback
                        
                    self.logger.info(f"   ✅ Перешли на вкладку товаров: {selector}")
                    tab_found = True
                    break
                except:
                    continue
            
            if not tab_found:
                self.logger.warning("   ⚠️ Вкладка товаров не найдена, ищем товары на основной странице")
            
            # Агрессивная прокрутка для загрузки всех товаров
            self.logger.info("   📜 Прокрутка для загрузки товаров...")
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            for i in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                try:
                    # Ждем изменения высоты или таймаута
                    WebDriverWait(self.driver, 1.5).until(
                        lambda d: d.execute_script("return document.body.scrollHeight") > last_height
                    )
                    last_height = self.driver.execute_script("return document.body.scrollHeight")
                except TimeoutException:
                    pass # Высота не изменилась, возможно конец списка
                
            # Дополнительная прокрутка внутри возможных контейнеров
            try:
                containers = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'scroll')]")
                for container in containers:
                    last_container_scroll = 0
                    for j in range(3):
                        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", container)
                        try:
                            # Небольшая пауза для прогрузки
                            time.sleep(0.5) 
                        except:
                            pass
            except:
                pass
            
            # Поиск товаров - расширенные селекторы
            self.logger.info("   🔍 Поиск элементов товаров...")
            product_elems = []
            
            # Сначала пробуем самые точные селекторы с таймаутом
            primary_selectors = [
                "//div[contains(@class, 'business-full-items-grouped-view__item')]",
                "//div[contains(@class, 'related-item-photo-view')]",
                "//div[contains(@class, 'related-item-list-view__item')]", 
                "//div[contains(@class, 'related-product-view')]"
            ]
            
            for selector in primary_selectors:
                start_time = time.time()
                try:
                    # Устанавливаем короткий таймаут для поиска
                    self.driver.implicitly_wait(2)
                    elems = self.driver.find_elements(By.XPATH, selector)
                    search_time = time.time() - start_time
                    
                    if elems:
                        product_elems = elems
                        self.logger.info(f"   📊 Найдено товаров с основным селектором '{selector}': {len(product_elems)} за {search_time:.2f}с")
                        break
                    else:
                        self.logger.debug(f"   🔍 Селектор '{selector}' не дал результатов за {search_time:.2f}с")
                        
                except Exception as e:
                    search_time = time.time() - start_time
                    self.logger.debug(f"   ❌ Ошибка селектора '{selector}' за {search_time:.2f}с: {e}")
                    continue
                finally:
                    # Возвращаем обычный таймаут
                    self.driver.implicitly_wait(5)
            
            # Если не нашли, пробуем дополнительные селекторы
            if not product_elems:
                additional_selectors = [
                    "//div[contains(@class, 'product-item')]",
                    "//div[contains(@class, 'service-item')]", 
                    "//div[contains(@class, 'price-item')]",
                    "//div[contains(@class, 'menu-item')]",
                    "//div[contains(@class, 'item') and contains(@class, 'related')]",
                    "//div[contains(@class, 'business-item')]",
                    "//div[contains(@class, 'card') and contains(@class, 'item')]",
                    "//li[contains(@class, 'item')]"
                ]
                
                for selector in additional_selectors:
                    try:
                        elems = self.driver.find_elements(By.XPATH, selector)
                        if elems:
                            product_elems = elems
                            self.logger.info(f"   📊 Найдено товаров с доп. селектором '{selector}': {len(product_elems)}")
                            break
                    except:
                        continue
                
            # Обрабатываем найденные товары
            if not product_elems:
                self.logger.warning("   ❌ Товары не найдены")
                return products
                
            # Ограничиваем количество товаров только при необходимости
            if self.max_products > 0 and len(product_elems) > self.max_products:
                product_elems = product_elems[:self.max_products]
                self.logger.info(f"   ✂️ Ограничиваем до {self.max_products} товаров")
            
            self.logger.info(f"   📊 Обрабатываем {len(product_elems)} товаров...")
            
            for i, elem in enumerate(product_elems, 1):
                try:
                    item_start_time = time.time()
                    self.logger.debug(f"      🔍 Обрабатываем товар {i}/{len(product_elems)}")
                    # Название - несколько селекторов
                    title = ""
                    # Быстрое получение атрибутов элемента
                    try:
                        elem_class = str(elem.get_attribute('class') or '')
                        elem_html = elem.get_attribute('outerHTML')[:200] or ''
                    except Exception as e:
                        self.logger.warning(f"      ⚠️ Ошибка получения атрибутов товара {i}: {e}")
                        elem_class = ''
                        elem_html = ''
                    
                    # Логируем тип элемента каждые 10 товаров для диагностики
                    if i <= 3 or i % 10 == 0:
                        self.logger.info(f"      🔍 Товар {i}: класс='{elem_class[:50]}', HTML содержит related-item-list-view: {'related-item-list-view' in elem_html}")
                    
                    if ('business-full-items-grouped-view__item' in elem_class or 
                        'related-item-list-view' in elem_html):
                        # Быстрые селекторы для списочного представления (оптимизированные)
                        title_selectors = [
                            ".//div[contains(@class, 'related-item-list-view__title')]",
                            ".//span[contains(@class, 'related-item-list-view__title')]",
                            ".//div[contains(@class, 'business-full-items-grouped-view__title')]",
                            ".//div[contains(@class, 'title')]",
                            ".//span[contains(@class, 'title')]"
                        ]
                    else:
                        # Селекторы для других типов элементов
                        title_selectors = [
                            ".//div[contains(@class, 'related-item-photo-view__title')]",
                            ".//div[contains(@class, 'related-item-list-view__title')]",
                            ".//div[contains(@class, 'product-title')]",
                            ".//div[contains(@class, 'service-title')]",
                            ".//div[contains(@class, 'item-title')]",
                            ".//div[contains(@class, 'business-title')]",
                            ".//span[contains(@class, 'title')]",
                            ".//a[contains(@class, 'title')]",
                            ".//h3", ".//h4", ".//h5",
                            ".//div[contains(@class, 'title')]",
                            ".//span[contains(@class, 'name')]",
                            ".//div[contains(@class, 'name')]",
                            ".//a[contains(@class, 'name')]",
                            ".//div[@title]"
                        ]
                    
                    # Оптимизированный поиск названия с кратким таймаутом
                    title_start_time = time.time()
                    for j, selector in enumerate(title_selectors):
                        selector_start = time.time()
                        try:
                            self.driver.implicitly_wait(0.5)  # Очень короткий таймаут
                            title_elem = elem.find_element(By.XPATH, selector)
                            title = title_elem.text.strip()
                            selector_time = time.time() - selector_start
                            
                            if title:
                                # Логируем успешный селектор для первых товаров
                                if i <= 3:
                                    self.logger.info(f"         📝 Название найдено селектором {j+1} за {selector_time:.3f}с: '{title[:30]}...'")
                                # Запоминаем успешный селектор для следующих товаров
                                if j > 0:  # Если нашли не первым селектором
                                    title_selectors[0], title_selectors[j] = title_selectors[j], title_selectors[0]
                                break
                            else:
                                if i <= 3:
                                    self.logger.debug(f"         📝 Селектор {j+1}: пустой за {selector_time:.3f}с")
                        except:
                            selector_time = time.time() - selector_start
                            if i <= 3:
                                self.logger.debug(f"         📝 Селектор {j+1}: ошибка за {selector_time:.3f}с")
                            continue
                        finally:
                            self.driver.implicitly_wait(5)  # Возвращаем обычный таймаут
                    
                    title_total_time = time.time() - title_start_time
                        
                    # Цена - адаптивные селекторы
                    price = ""
                    if ('business-full-items-grouped-view__item' in elem_class or 
                        'related-item-list-view' in elem_html):
                        # Быстрые селекторы цен для списочного представления (оптимизированные)
                        price_selectors = [
                            ".//div[contains(@class, 'related-item-list-view__price')]",
                            ".//span[contains(@class, 'related-item-list-view__price')]",
                            ".//div[contains(@class, 'business-full-items-grouped-view__price')]",
                            ".//div[contains(@class, 'price')]",
                            ".//span[contains(@class, 'price')]",
                            ".//div[contains(text(), '₽')]",
                            ".//span[contains(text(), '₽')]"
                        ]
                    else:
                        # Селекторы для других типов элементов  
                        price_selectors = [
                            ".//span[contains(@class, 'related-product-view__price')]",
                            ".//div[contains(@class, 'related-product-view__price')]",
                            ".//span[contains(@class, 'related-item-list-view__price')]",
                            ".//div[contains(@class, 'related-item-list-view__price')]",
                            ".//span[contains(@class, 'price')]",
                            ".//div[contains(@class, 'price')]",
                            ".//span[contains(@class, 'cost')]",
                            ".//div[contains(@class, 'cost')]",
                            ".//span[contains(@class, 'value')]",
                            ".//div[contains(@class, 'value')]",
                            ".//span[contains(@class, 'amount')]",
                            ".//div[contains(@class, 'amount')]",
                            ".//span[contains(@class, 'rub')]",
                            ".//div[contains(@class, 'rub')]",
                            ".//span[contains(@class, '₽')]",
                            ".//div[contains(@class, '₽')]"
                        ]
                    
                    # Оптимизированный поиск цены с кратким таймаутом
                    price_start_time = time.time()
                    for k, selector in enumerate(price_selectors):
                        selector_start = time.time()
                        try:
                            self.driver.implicitly_wait(0.5)  # Очень короткий таймаут
                            price_elem = elem.find_element(By.XPATH, selector)
                            price = price_elem.text.strip()
                            selector_time = time.time() - selector_start
                            
                            if price:
                                # Логируем успешный селектор для первых товаров
                                if i <= 3:
                                    self.logger.info(f"         💰 Цена найдена селектором {k+1} за {selector_time:.3f}с: '{price}'")
                                # Запоминаем успешный селектор для следующих товаров
                                if k > 0:  # Если нашли не первым селектором
                                    price_selectors[0], price_selectors[k] = price_selectors[k], price_selectors[0]
                                break
                            else:
                                if i <= 3:
                                    self.logger.debug(f"         💰 Селектор {k+1}: пустой за {selector_time:.3f}с")
                        except:
                            selector_time = time.time() - selector_start
                            if i <= 3:
                                self.logger.debug(f"         💰 Селектор {k+1}: ошибка за {selector_time:.3f}с")
                            continue
                        finally:
                            self.driver.implicitly_wait(5)  # Возвращаем обычный таймаут
                    
                    price_total_time = time.time() - price_start_time
                    
                    # Описание - быстрый поиск с таймаутом
                    description = ""
                    try:
                        # Короткий таймаут для описания
                        self.driver.implicitly_wait(0.5)
                        desc_elem = elem.find_element(By.XPATH, ".//div[contains(@class, 'description')] | .//p")
                        description = desc_elem.text.strip()
                    except:
                        description = ""  # Если не найдено, оставляем пустым
                    finally:
                        self.driver.implicitly_wait(5)  # Возвращаем обычный таймаут
                    
                    # Добавляем только если есть название или цена
                    if title or price:
                        product_data = {
                            'title': title,
                            'price': price,
                            'description': description
                        }
                        products.append(product_data)
                        total_extraction_time = title_total_time + price_total_time
                        total_item_time = time.time() - item_start_time
                        
                        # Логируем время для первых 3 товаров
                        if i <= 3:
                            self.logger.info(f"   ✅ Товар {i}: {title} - {price} (извлечение: {total_extraction_time:.3f}с, общее: {total_item_time:.3f}с)")
                        else:
                            self.logger.info(f"   ✅ Товар {i}: {title} - {price}")
                        
                        # Промежуточный прогресс каждые 10 товаров
                        if i % 10 == 0:
                            self.logger.info(f"   📈 Прогресс: {i}/{len(product_elems)} товаров обработано")
                    else:
                        # Отладочная информация
                        try:
                            elem_html = elem.get_attribute('outerHTML')[:200]
                            self.logger.warning(f"   ⚠️ Товар {i}: пустые данные. HTML: {elem_html}...")
                        except:
                            self.logger.warning(f"   ⚠️ Товар {i}: пустые данные")
                    
                except Exception as e:
                    self.logger.error(f"   ❌ Ошибка товара {i}: {e}")
                    continue
                        
        except Exception as e:
            self.logger.error(f"   ❌ Ошибка поиска товаров: {e}")
        
        self.logger.info(f"✅ Извлечено товаров: {len(products)}")
        return products
    

    
    def extract_yandex_id(self, url):
        try:
            match = re.search(r'/org/.+?/(\d+)/', url)
            return match.group(1) if match else ""
        except:
            return ""
    
    def find_element_by_selectors(self, selectors):
        for selector in selectors:
            try:
                if '/@' in selector:
                    xpath_parts = selector.split('/@')
                    element = self.driver.find_element(By.XPATH, xpath_parts[0])
                    return element
                else:
                    return self.driver.find_element(By.XPATH, selector)
            except:
                continue
        return None
    
    def find_element_by_selectors_with_timeout(self, selectors: List[str], timeout: int = 10) -> Optional[WebElement]:
        """Поиск элемента с таймаутом"""
        
        for selector in selectors:
            try:
                if '/@' in selector:
                    xpath_parts = selector.split('/@')
                    element = WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.XPATH, xpath_parts[0]))
                    )
                    return element
                else:
                    element = WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    return element
            except:
                continue
        return None
    
    def extract_by_selectors(self, selectors):
        for selector in selectors:
            try:
                if '/@' in selector:
                    xpath_parts = selector.split('/@')
                    element = self.driver.find_element(By.XPATH, xpath_parts[0])
                    text = element.get_attribute(xpath_parts[1])
                    if text:
                        return text.strip()
                else:
                    element = self.driver.find_element(By.XPATH, selector)
                    text = element.text.strip()
                    if text:
                        return text
            except:
                continue
        return ""
    

    
    def save_business_data(self, business_url, data, interrupted=False):
        try:
            business_name = data.get('name', 'unknown')
            yandex_id = data.get('yandex_id', 'unknown')
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', business_name)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Создаем отдельную папку для каждого предприятия в папке сессии
            business_folder = f"{self.session_folder}/{safe_name}_{yandex_id}"
            os.makedirs(business_folder, exist_ok=True)
            
            # Добавляем префикс если прервано
            prefix = "INTERRUPTED_" if interrupted else ""
            filename = f"{prefix}{safe_name}_{yandex_id}_{timestamp}"
            
            # JSON файл
            json_filename = f"{business_folder}/{filename}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # CSV файл
            csv_filename = f"{business_folder}/{filename}.csv"
            self.save_to_csv(csv_filename, data)
            
            if interrupted:
                self.logger.info(f"💾 Данные сохранены при прерывании:")
            else:
                self.logger.info(f"💾 Данные сохранены:")
            self.logger.info(f"   📄 JSON: {json_filename}")
            self.logger.info(f"   📊 CSV: {csv_filename}")
            
            return json_filename, csv_filename
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения: {e}")
            return None, None
    
    def save_to_csv(self, filename, data):
        try:
            # Создаем основной CSV с базовой информацией
            basic_data = {k: v for k, v in data.items() if k not in ['products_and_services']}
            basic_data['products_count'] = len(data.get('products_and_services', []))
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=basic_data.keys())
                writer.writeheader()
                writer.writerow(basic_data)
            
            # Создаем отдельные CSV файлы для товаров и отзывов
            base_name = filename.replace('.csv', '')
            
            # CSV для товаров и услуг
            if data.get('products_and_services'):
                products_filename = f"{base_name}_products.csv"
                with open(products_filename, 'w', newline='', encoding='utf-8') as csvfile:
                    if data['products_and_services']:
                        fieldnames = data['products_and_services'][0].keys()
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        for product in data['products_and_services']:
                            writer.writerow(product)
                self.logger.info(f"✅ CSV товаров создан: {products_filename}")
            

            
            self.logger.info(f"✅ Основной CSV файл создан: {filename}")
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения CSV: {e}")
    
    def flatten_dict(self, d, parent_key='', sep='_'):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                if v and isinstance(v[0], dict):
                    # Для списков словарей создаем отдельные колонки
                    if k == 'products_and_services':
                        for i, item in enumerate(v):
                            if isinstance(item, dict):
                                for sub_k, sub_v in item.items():
                                    col_name = f"{new_key}_{i+1}_{sub_k}"
                                    items.append((col_name, str(sub_v)))
                            else:
                                items.append((f"{new_key}_{i+1}", str(item)))
                    
                    else:
                        items.append((new_key, f"{len(v)} items"))
                else:
                    items.append((new_key, '; '.join(map(str, v))))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def parse_single_business(self, business_url):
        try:
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"🔍 ПАРСИНГ ОДНОГО ПРЕДПРИЯТИЯ")
            self.logger.info(f"{'='*60}")
            self.logger.info(f"URL: {business_url}")
            
            # Очищаем URL от лишних частей
            clean_url = business_url.split('/gallery/')[0].split('/reviews/')[0].split('/photos/')[0]
            if not clean_url.endswith('/'):
                clean_url += '/'
            
            self.logger.info(f"Очищенный URL: {clean_url}")
            
            # Сохраняем URL для обработчика сигналов
            self.business_url = clean_url
            
            # Проверяем, есть ли уже WebDriver
            if not self.driver:
                if not self.setup_driver():
                    return None
            
            self.driver.get(clean_url)
            
            # Ожидание загрузки (оптимизация WebDriverWait)
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//h1"))
                )
            except TimeoutException:
                self.logger.warning("⚠️ Страница загружалась долго, продолжаем...")
                
            self.logger.info("✅ Страница предприятия загружена")
            
            data = {
                'url': business_url,
                'extraction_date': datetime.now().isoformat(),
                'yandex_id': self.extract_yandex_id(business_url)
            }
            
            # Сохраняем текущие данные для обработчика сигналов
            self.current_data = data
            
            # Этапы извлечения
            stages = [
                ("📝 Базовая информация", self.extract_basic_info),
                ("📞 Контактная информация", self.extract_contact_info),
                ("🛍️ Товары и услуги", self.extract_all_products_and_services)
            ]
            
            for i, (stage_name, stage_func) in enumerate(stages, 1):
                self.logger.info(f"\n🔄 ЭТАП {i}/{len(stages)}: {stage_name}")
                self.logger.info("=" * 50)
                
                start_time = time.time()
                try:
                    if stage_name == "🛍️ Товары и услуги":
                        result = stage_func()
                        data['products_and_services'] = result
                        self.logger.info(f"   📊 Найдено товаров: {len(result) if result else 0}")
                    else:
                        result = stage_func()
                        data.update(result)
                    
                    # Обновляем текущие данные после каждого этапа
                    self.current_data = data
                    
                    elapsed = time.time() - start_time
                    self.logger.info(f"✅ {stage_name} - ЗАВЕРШЕН за {elapsed:.1f}с")
                    
                except Exception as e:
                    self.logger.error(f"❌ Ошибка на этапе {stage_name}: {e}")
                    if stage_name == "🛍️ Товары и услуги":
                        data['products_and_services'] = []
                    
                    # Обновляем текущие данные даже при ошибке
                    self.current_data = data
            
            if data.get('name'):
                self.logger.info(f"✅ {data['name']} - данные собраны успешно")
                self.save_business_data(business_url, data)
                # Очищаем данные после успешного сохранения
                self.current_data = None
                self.business_url = None
                return data
            else:
                self.logger.warning(f"❌ Данные не извлечены")
                # Очищаем данные если ничего не извлечено
                self.current_data = None
                self.business_url = None
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка обработки {business_url}: {e}")
            return None
    
    def run(self, business_url):
        try:
            # Проверяем, есть ли уже WebDriver
            if not self.driver:
                if not self.setup_driver():
                    return False
            
            data = self.parse_single_business(business_url)
            
            if data:
                self.logger.info(f"\n🎉 ПАРСИНГ ЗАВЕРШЕН УСПЕШНО")
                self.logger.info(f"📊 Статистика:")
                self.logger.info(f"   📝 Название: {data.get('name', 'N/A')}")
                self.logger.info(f"   📍 Адрес: {data.get('address', 'N/A')}")
                self.logger.info(f"   📱 Телефоны: {len(data.get('phones', []))}")
                self.logger.info(f"   🛍️ Товары/услуги: {len(data.get('products_and_services', []))}")
                return True
            else:
                self.logger.error(f"❌ ПАРСИНГ НЕ УДАЛСЯ")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка: {e}")
            return False
        
        finally:
            # Закрываем WebDriver только если мы его создавали
            if self.driver and not hasattr(self, '_external_driver'):
                self.driver.quit()
                self.logger.info("🔚 WebDriver закрыт")
            # Очищаем данные при завершении
            self.current_data = None
            self.business_url = None


def main():
    # URL для тестирования (одно предприятие)
    business_url = "https://yandex.ru/maps/org/univerdent/197682062365/"
    
    print("🚀 Запуск парсера одного предприятия")
    print("💡 Для прерывания нажмите Ctrl+C - данные будут сохранены автоматически")
    print("=" * 60)
    
    parser = SingleBusinessParser()
    parser.run(business_url)

# Добавляем метод close к классу SingleBusinessParser
def close_method(self):
    """Закрытие драйвера"""
    if hasattr(self, '_external_driver') and self._external_driver:
        # Не закрываем внешний драйвер
        self.logger.info("🔗 Используется внешний WebDriver, не закрываем")
        return
        
    if self.driver:
        try:
            self.driver.quit()
            self.logger.info("🔒 WebDriver закрыт")
        except Exception as e:
            self.logger.error(f"❌ Ошибка закрытия WebDriver: {e}")
    else:
        self.logger.warning("⚠️ WebDriver уже закрыт или не был инициализирован")

# Привязываем метод к классу
SingleBusinessParser.close = close_method

if __name__ == "__main__":
    main()
