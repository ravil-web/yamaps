#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Комплексный парсер Яндекс Карт
Собирает ВСЮ информацию из карточки предприятия, включая все вкладки
"""

import time
import json
import os
import re
import csv
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class YandexMapsComprehensiveParser:
    def __init__(self, target_count=3):
        self.driver = None
        self.target_count = target_count
        self.businesses = []
        self.processed_urls = set()
        
        # Настройка логгирования
        self.setup_logging()
    
    def setup_logging(self):
        """Настройка системы логгирования"""
        # Создаем папку для логов
        os.makedirs("logs", exist_ok=True)
        
        # Настройка форматирования
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Файловый логгер
        file_handler = logging.FileHandler(
            f'logs/parser_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Консольный логгер
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Основной логгер
        self.logger = logging.getLogger('YandexParser')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info("🚀 Система логгирования инициализирована")
        
    def setup_driver(self):
        """Настройка WebDriver"""
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
    
    def navigate_to_search(self, url):
        """Переход к странице поиска"""
        try:
            self.logger.info(f"🔍 Переход к странице поиска: {url}")
            self.driver.get(url)
            time.sleep(3)
            self.logger.info("✅ Страница поиска загружена")
            return True
        except Exception as e:
            self.logger.error(f"❌ Ошибка перехода к странице поиска: {e}")
            return False
    
    def get_business_urls(self):
        """Получение прямых ссылок на предприятия (только основные, без дубликатов)"""
        business_urls = []
        
        try:
            # Ищем только основные ссылки на организации (без /gallery/, /reviews/ и т.д.)
            selectors = [
                "//a[contains(@href, '/org/') and not(contains(@href, '/gallery/') or contains(@href, '/reviews/') or contains(@href, '/chain/') or contains(@href, '/features/'))]",
                "//div[contains(@class, 'search-business-snippet-view')]//a[contains(@href, '/org/') and not(contains(@href, '/gallery/') or contains(@href, '/reviews/'))]",
                "//div[contains(@class, 'search-snippet-view')]//a[contains(@href, '/org/') and not(contains(@href, '/gallery/') or contains(@href, '/reviews/'))]"
            ]
            
            for selector in selectors:
                try:
                    self.logger.debug(f"🔍 Поиск по селектору: {selector}")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    self.logger.debug(f"   Найдено элементов: {len(elements)}")
                    
                    for elem in elements:
                        href = elem.get_attribute('href')
                        if href and '/org/' in href and href not in business_urls:
                            # Проверяем, что это основная ссылка (не вкладка)
                            if not any(x in href for x in ['/gallery/', '/reviews/', '/chain/', '/features/', '/posts/']):
                                business_urls.append(href)
                                self.logger.info(f"   📌 Найдена ссылка: {href}")
                    
                    if len(business_urls) >= self.target_count:
                        self.logger.info(f"   ✅ Достигнуто целевое количество: {self.target_count}")
                        break
                except Exception as e:
                    self.logger.warning(f"   ⚠️ Ошибка при поиске по селектору {selector}: {e}")
                    continue
            
            self.logger.info(f"📊 Найдено уникальных ссылок: {len(business_urls)}")
            return business_urls[:self.target_count]
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения ссылок: {e}")
            return []
    
    def scroll_and_collect_more(self, current_urls):
        """Прокрутка для загрузки дополнительных предприятий"""
        try:
            # Ищем контейнер для прокрутки
            scroll_containers = [
                "//div[contains(@class, 'search-list-view')]",
                "//div[contains(@class, 'search-results')]",
                "//div[contains(@class, 'scroll')]"
            ]
            
            container = None
            for selector in scroll_containers:
                try:
                    container = self.driver.find_element(By.XPATH, selector)
                    break
                except:
                    continue
            
            if container:
                self.logger.info("📜 Прокрутка контейнера для загрузки новых элементов...")
                # Прокручиваем контейнер
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", container)
                time.sleep(2)
                
                # Проверяем новые URL
                new_urls = self.get_business_urls()
                unique_new = [url for url in new_urls if url not in current_urls]
                self.logger.info(f"🔄 Найдено новых ссылок после прокрутки: {len(unique_new)}")
                return new_urls
            
        except Exception as e:
            self.logger.warning(f"⚠️ Ошибка прокрутки: {e}")
        
        return current_urls
    
    def collect_all_business_urls(self):
        """Сбор всех URL предприятий с прокруткой"""
        all_urls = []
        
        self.logger.info(f"🎯 Цель: собрать {self.target_count} предприятий")
        
        while len(all_urls) < self.target_count:
            current_urls = self.get_business_urls()
            
            if not current_urls:
                self.logger.error("❌ Не найдено ссылок на предприятия")
                break
            
            # Добавляем новые URL
            for url in current_urls:
                if url not in all_urls:
                    all_urls.append(url)
            
            self.logger.info(f"📈 Всего собрано: {len(all_urls)}/{self.target_count}")
            
            if len(all_urls) >= self.target_count:
                break
                
            # Прокрутка для загрузки новых элементов
            new_urls = self.scroll_and_collect_more(all_urls)
            
            # Если новых URL не появилось, пробуем еще раз
            if len(new_urls) <= len(all_urls):
                self.logger.info("🔄 Попытка дополнительной прокрутки...")
                time.sleep(1)
                final_urls = self.scroll_and_collect_more(all_urls)
                
                if len(final_urls) <= len(all_urls):
                    self.logger.warning("⚠️ Достигнут конец списка результатов")
                    break
                else:
                    all_urls = final_urls
        
        self.logger.info(f"✅ Сбор URL завершен. Итого: {len(all_urls)} предприятий")
        return all_urls[:self.target_count]
    
    def extract_basic_info(self):
        """Извлечение базовой информации"""
        data = {}
        
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
            
            # Рейтинг и отзывы
            rating_elem = self.find_element_by_selectors([
                "//span[contains(@class, 'business-rating-badge-view__rating-text')]"
            ])
            data['rating'] = rating_elem.text.strip() if rating_elem else ""
            self.logger.info(f"   ⭐ Рейтинг: {data['rating']}")
            
            reviews_elem = self.find_element_by_selectors([
                "//div[contains(@class, 'business-header-rating-view__text')]"
            ])
            data['reviews_count'] = reviews_elem.text.strip() if reviews_elem else ""
            self.logger.info(f"   💬 Отзывов: {data['reviews_count']}")
            
            # Верификация
            verification_elem = self.find_element_by_selectors([
                "//span[contains(@class, 'business-verified-badge')]"
            ])
            data['verified'] = verification_elem is not None
            self.logger.info(f"   ✅ Верифицировано: {data['verified']}")
            
            # Адрес
            address_selectors = [
                "//div[contains(@class, 'business-contacts-view__address-link')]",
                "//meta[@itemprop='address']/@content"
            ]
            data['address'] = self.extract_by_selectors(address_selectors)
            self.logger.info(f"   📍 Адрес: {data['address']}")
            
            self.logger.info("✅ Базовая информация извлечена успешно")
            return data
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения базовой информации: {e}")
            return {}
    
    def extract_contact_info(self):
        """Извлечение контактной информации"""
        contacts = {}
        
        try:
            self.logger.info("📞 Извлечение контактной информации...")
            # Телефоны
            phones = []
            phone_selectors = [
                "//span[@itemprop='telephone']",
                "//div[contains(@class, 'card-phones-view__number')]//span",
                "//div[contains(@class, 'card-phones-view__phone-number')]"
            ]
            
            phone_elements = []
            for selector in phone_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    phone_elements.extend(elements)
                except:
                    continue
                    
            for elem in phone_elements:
                phone = elem.text.strip() if elem.text else elem.get_attribute('textContent')
                if phone and phone not in phones:
                    phones.append(phone)
            
            contacts['phones'] = phones
            self.logger.info(f"   📱 Телефоны: {phones}")
            
            # Сайт
            website_selectors = [
                "//a[contains(@class, 'business-urls-view__link')][@itemprop='url']",
                "//a[contains(@class, 'business-urls-view__link')]"
            ]
            website_elem = self.find_element_by_selectors(website_selectors)
            contacts['website'] = website_elem.get_attribute('href') if website_elem else ""
            self.logger.info(f"   🌐 Сайт: {contacts['website']}")
            
            # Социальные сети
            social_links = []
            social_selectors = [
                "//div[contains(@class, 'business-contacts-view__social-button')]//a[@itemprop='sameAs']",
                "//div[contains(@class, 'business-contacts-view__social-button')]//a"
            ]
            
            social_elements = []
            for selector in social_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    social_elements.extend(elements)
                except:
                    continue
                    
            for elem in social_elements:
                href = elem.get_attribute('href')
                if href and href not in social_links:
                    social_links.append(href)
            
            contacts['social_links'] = social_links
            self.logger.info(f"   📱 Соцсети: {social_links}")
            
            # Время работы (базовое)
            working_hours_selectors = [
                "//div[contains(@class, 'business-card-working-status-view__text')]",
                "//meta[@itemprop='openingHours']/@content"
            ]
            contacts['working_hours'] = self.extract_by_selectors(working_hours_selectors)
            self.logger.info(f"   🕐 Время работы: {contacts['working_hours']}")
            
            # Детальный график работы из блока business-dialog-view__content
            contacts['detailed_schedule'] = self.extract_detailed_schedule()
            self.logger.info(f"   📅 Детальный график: {len(contacts['detailed_schedule'])} дней")
            
            self.logger.info("✅ Контактная информация извлечена успешно")
            return contacts
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения контактов: {e}")
            return {}
    
    def extract_detailed_schedule(self):
        """Извлечение детального графика работы из блока business-dialog-view__content"""
        schedule = {}
        
        try:
            self.logger.debug("📅 Поиск детального графика работы...")
            # Ищем блок с графиком работы
            schedule_selectors = [
                "//div[contains(@class, 'business-dialog-view__content')]//div[contains(@class, 'business-working-status-view')]",
                "//div[contains(@class, 'business-dialog-view__content')]//div[contains(@class, 'working-hours')]",
                "//div[contains(@class, 'business-dialog-view__content')]//div[contains(@class, 'schedule')]"
            ]
            
            for selector in schedule_selectors:
                try:
                    schedule_elements = self.driver.find_elements(By.XPATH, selector)
                    if schedule_elements:
                        for elem in schedule_elements:
                            # Извлекаем дни недели и время
                            day_elements = elem.find_elements(By.XPATH, ".//div[contains(@class, 'day') or contains(@class, 'weekday')]")
                            time_elements = elem.find_elements(By.XPATH, ".//div[contains(@class, 'time') or contains(@class, 'hours')]")
                            
                            for i, day_elem in enumerate(day_elements):
                                day = day_elem.text.strip()
                                time_text = ""
                                if i < len(time_elements):
                                    time_text = time_elements[i].text.strip()
                                
                                if day:
                                    schedule[day] = time_text
                        
                        if schedule:
                            break
                except:
                    continue
            
            # Если не нашли в dialog, ищем в основном контенте
            if not schedule:
                main_schedule_selectors = [
                    "//div[contains(@class, 'business-working-status-view')]//div[contains(@class, 'day')]",
                    "//div[contains(@class, 'working-hours')]//div[contains(@class, 'day')]"
                ]
                
                for selector in main_schedule_selectors:
                    try:
                        day_elements = self.driver.find_elements(By.XPATH, selector)
                        for elem in day_elements:
                            text = elem.text.strip()
                            if text and ':' in text:
                                # Парсим "Пн-Пт: 9:00-18:00" или "Понедельник: 9:00-18:00"
                                parts = text.split(':', 1)
                                if len(parts) == 2:
                                    day = parts[0].strip()
                                    time_text = parts[1].strip()
                                    schedule[day] = time_text
                    except:
                        continue
            
            self.logger.debug(f"📅 Найдено дней в графике: {len(schedule)}")
            return schedule
            
        except Exception as e:
            self.logger.warning(f"❌ Ошибка извлечения графика работы: {e}")
            return {}
    
    def extract_features_and_services(self):
        """Извлечение особенностей и услуг"""
        features = {}
        
        try:
            self.logger.info("🔧 Извлечение особенностей и услуг...")
            
            # Особенности (да/нет)
            bool_features = []
            bool_selectors = [
                "//div[contains(@class, 'business-features-view__bool-text')]",
                "//div[contains(@class, 'features-view__bool-text')]",
                "//div[contains(@class, 'bool-feature')]"
            ]
            
            for selector in bool_selectors:
                try:
                    bool_elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in bool_elements:
                        text = elem.text.strip()
                        if text and text not in bool_features:
                            bool_features.append(text)
                except:
                    continue
            
            features['boolean_features'] = bool_features
            self.logger.info(f"   ✅ Булевы особенности: {len(bool_features)}")
            
            # Подробные услуги
            valued_features = {}
            valued_selectors = [
                "//div[contains(@class, 'business-features-view__valued')]",
                "//div[contains(@class, 'features-view__valued')]",
                "//div[contains(@class, 'valued-feature')]"
            ]
            
            for selector in valued_selectors:
                try:
                    valued_elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in valued_elements:
                        try:
                            title_elem = elem.find_element(By.XPATH, ".//span[contains(@class, 'business-features-view__valued-title')]")
                            value_elem = elem.find_element(By.XPATH, ".//span[contains(@class, 'business-features-view__valued-value')]")
                            
                            if title_elem and value_elem:
                                title = title_elem.text.strip().rstrip(':')
                                value = value_elem.text.strip()
                                if title and value:
                                    valued_features[title] = value
                        except:
                            continue
                except:
                    continue
            
            features['detailed_features'] = valued_features
            self.logger.info(f"   ✅ Детальные особенности: {len(valued_features)}")
            
            # Категории
            categories = []
            category_selectors = [
                "//a[contains(@class, 'business-categories-view__category')]",
                "//div[contains(@class, 'categories-view__category')]",
                "//span[contains(@class, 'category')]"
            ]
            
            for selector in category_selectors:
                try:
                    category_elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in category_elements:
                        text = elem.text.strip()
                        if text and text not in categories:
                            categories.append(text)
                except:
                    continue
            
            features['categories'] = categories
            self.logger.info(f"   ✅ Категории: {len(categories)}")
            
            self.logger.info("✅ Особенности и услуги извлечены успешно")
            return features
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения особенностей: {e}")
            return {}
    
    def extract_media_content(self):
        """Извлечение медиа-контента"""
        media = {}
        
        try:
            self.logger.info("🖼️ Извлечение медиа-контента...")
            
            # Фотографии
            photos = []
            photo_selectors = [
                "//img[contains(@class, 'orgpage-media-view__media')]",
                "//img[contains(@src, 'avatars.mds.yandex.net')]",
                "//div[contains(@class, 'orgpage-media-view__item')]//img",
                "//img[contains(@class, 'media')]",
                "//div[contains(@class, 'gallery')]//img"
            ]
            
            for selector in photo_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        src = elem.get_attribute('src')
                        alt = elem.get_attribute('alt')
                        if src and src not in [p['url'] for p in photos]:
                            photos.append({
                                'url': src,
                                'alt': alt or ""
                            })
                except:
                    continue
            
            media['photos'] = photos
            self.logger.info(f"   📸 Фотографии: {len(photos)}")
            
            # Видео
            videos = []
            video_selectors = [
                "//div[contains(@class, 'video-thumbnail')]",
                "//div[contains(@class, 'video')]",
                "//video"
            ]
            
            for selector in video_selectors:
                try:
                    video_elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in video_elements:
                        try:
                            video_data = elem.get_attribute('data-video-src')
                            if video_data and video_data not in videos:
                                videos.append(video_data)
                        except:
                            continue
                except:
                    continue
            
            media['videos'] = videos
            self.logger.info(f"   🎥 Видео: {len(videos)}")
            
            # Панорама
            panorama_selectors = [
                "//button[contains(@class, 'card-media-preview _type_panorama')]",
                "//div[contains(@class, 'panorama-thumbnail-view')]",
                "//div[contains(@class, 'panorama')]"
            ]
            
            has_panorama = False
            for selector in panorama_selectors:
                try:
                    panorama_elem = self.driver.find_element(By.XPATH, selector)
                    if panorama_elem:
                        has_panorama = True
                        break
                except:
                    continue
            
            media['has_panorama'] = has_panorama
            self.logger.info(f"   🏙️ Панорама: {has_panorama}")
            
            self.logger.info("✅ Медиа-контент извлечен успешно")
            return media
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения медиа: {e}")
            return {}
    
    def navigate_to_tab(self, tab_name):
        """Переход к конкретной вкладке"""
        try:
            self.logger.info(f"🔄 Попытка перехода на вкладку: {tab_name}")
            
            tab_selectors = {
                'prices': [
                    "//div[@class='tabs-select-view__title _name_prices']",
                    "//div[contains(@class, 'tabs-select-view__title') and contains(text(), 'Товары')]",
                    "//div[contains(@class, 'tabs-select-view__title') and contains(text(), 'Услуги')]"
                ],
                'reviews': [
                    "//div[@class='tabs-select-view__title _name_reviews']",
                    "//div[contains(@class, 'tabs-select-view__title') and contains(text(), 'Отзывы')]"
                ], 
                'gallery': [
                    "//div[@class='tabs-select-view__title _name_gallery']",
                    "//div[contains(@class, 'tabs-select-view__title') and contains(text(), 'Фото')]"
                ],
                'posts': [
                    "//div[@class='tabs-select-view__title _name_posts']"
                ],
                'chain': [
                    "//div[@class='tabs-select-view__title _name_chain']",
                    "//div[contains(@class, 'tabs-select-view__title') and contains(text(), 'Филиалы')]"
                ],
                'features': [
                    "//div[@class='tabs-select-view__title _name_features']",
                    "//div[contains(@class, 'tabs-select-view__title') and contains(text(), 'Особенности')]"
                ]
            }
            
            if tab_name in tab_selectors:
                for selector in tab_selectors[tab_name]:
                    try:
                        self.logger.debug(f"   🔍 Поиск вкладки по селектору: {selector}")
                        tab_elem = self.driver.find_element(By.XPATH, selector)
                        if tab_elem and tab_elem.is_displayed():
                            self.logger.info(f"   ✅ Найдена вкладка {tab_name}, кликаем...")
                            self.driver.execute_script("arguments[0].click();", tab_elem)
                            time.sleep(3)  # Увеличиваем время ожидания
                            self.logger.info(f"✅ Перешли на вкладку: {tab_name}")
                            return True
                    except Exception as e:
                        self.logger.debug(f"   ⚠️ Селектор {selector} не найден: {e}")
                        continue
            
            self.logger.warning(f"❌ Вкладка {tab_name} не найдена")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка перехода на вкладку {tab_name}: {e}")
            return False
    
    def extract_products_and_services(self):
        """Извлечение товаров и услуг с ценами"""
        products = []
        
        try:
            self.logger.info("🛍️ Извлечение товаров и услуг...")
            
            # Переход на вкладку товаров и услуг
            self.logger.info("   🔄 Попытка перехода на вкладку товаров и услуг...")
            if self.navigate_to_tab('prices'):
                time.sleep(3)
                self.logger.info("   ✅ Переход на вкладку товаров и услуг выполнен")
            else:
                self.logger.warning("   ⚠️ Не удалось перейти на вкладку товаров и услуг")
                return products
            
            # Поиск товаров и услуг с множественными селекторами
            product_selectors = [
                "//div[contains(@class, 'related-product-view')]",
                "//div[contains(@class, 'card-related-products-view')]//div[contains(@class, 'related-item-photo-view')]",
                "//div[contains(@class, 'related-item-photo-view')]",
                "//div[contains(@class, 'product-item')]",
                "//div[contains(@class, 'service-item')]"
            ]
            
            self.logger.info("   🔍 Поиск элементов товаров и услуг...")
            product_elements = []
            for j, selector in enumerate(product_selectors, 1):
                try:
                    self.logger.info(f"   📍 Селектор {j}/{len(product_selectors)}: {selector}")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    self.logger.info(f"   📦 Найдено элементов: {len(elements)}")
                    product_elements.extend(elements)
                except Exception as e:
                    self.logger.warning(f"   ⚠️ Ошибка селектора {selector}: {e}")
                    continue
            
            self.logger.info(f"   📊 Всего найдено элементов товаров: {len(product_elements)}")
            
            if not product_elements:
                self.logger.info("   ℹ️ Товары и услуги не найдены")
                return products
            
            self.logger.info("   🔄 Обработка найденных товаров...")
            for i, elem in enumerate(product_elements, 1):
                try:
                    self.logger.info(f"   📦 Товар {i}/{len(product_elements)} - обработка...")
                    
                    # Название
                    title_selectors = [
                        ".//div[contains(@class, 'related-item-photo-view__title')]",
                        ".//div[contains(@class, 'product-title')]",
                        ".//div[contains(@class, 'service-title')]",
                        ".//h3",
                        ".//h4"
                    ]
                    
                    title = ""
                    for title_selector in title_selectors:
                        try:
                            title_elem = elem.find_element(By.XPATH, title_selector)
                            title = title_elem.text.strip()
                            if title:
                                break
                        except:
                            continue
                    
                    # Описание
                    desc_selectors = [
                        ".//div[contains(@class, 'related-item-photo-view__description')]",
                        ".//div[contains(@class, 'product-description')]",
                        ".//div[contains(@class, 'service-description')]",
                        ".//p"
                    ]
                    
                    description = ""
                    for desc_selector in desc_selectors:
                        try:
                            desc_elem = elem.find_element(By.XPATH, desc_selector)
                            description = desc_elem.text.strip()
                            if description:
                                break
                        except:
                            continue
                    
                    # Цена
                    price_selectors = [
                        ".//span[contains(@class, 'related-product-view__price')]",
                        ".//span[contains(@class, 'price')]",
                        ".//div[contains(@class, 'price')]"
                    ]
                    
                    price = ""
                    for price_selector in price_selectors:
                        try:
                            price_elem = elem.find_element(By.XPATH, price_selector)
                            price = price_elem.text.strip()
                            if price:
                                break
                        except:
                            continue
                    
                    # Изображение
                    try:
                        img_elem = elem.find_element(By.XPATH, ".//img")
                        image_url = img_elem.get_attribute('src') if img_elem else ""
                    except:
                        image_url = ""
                    
                    if title:
                        product_data = {
                            'title': title,
                            'description': description,
                            'price': price,
                            'image_url': image_url
                        }
                        products.append(product_data)
                        self.logger.info(f"   ✅ Товар {i}: {title}")
                    else:
                        self.logger.warning(f"   ⚠️ Товар {i}: название не найдено")
                        
                except Exception as e:
                    self.logger.error(f"   ❌ Ошибка обработки товара {i}: {e}")
                    continue
            
            self.logger.info(f"✅ Извлечено товаров и услуг: {len(products)}")
            return products
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения товаров и услуг: {e}")
            return []
    
    def extract_reviews(self):
        """Извлечение отзывов"""
        reviews = []
        
        try:
            self.logger.info("⭐ Извлечение отзывов...")
            
            # Переход на вкладку отзывов
            self.logger.info("   🔄 Попытка перехода на вкладку отзывов...")
            if self.navigate_to_tab('reviews'):
                time.sleep(3)
                self.logger.info("   ✅ Переход на вкладку отзывов выполнен")
            else:
                self.logger.warning("   ⚠️ Не удалось перейти на вкладку отзывов")
                return reviews
            
            # Поиск отзывов с множественными селекторами
            review_selectors = [
                "//div[contains(@class, 'business-review-view')]",
                "//div[contains(@class, 'review-view')]",
                "//div[contains(@class, 'review-item')]"
            ]
            
            self.logger.info("   🔍 Поиск элементов отзывов...")
            review_elements = []
            for j, selector in enumerate(review_selectors, 1):
                try:
                    self.logger.info(f"   📍 Селектор {j}/{len(review_selectors)}: {selector}")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    self.logger.info(f"   📝 Найдено отзывов: {len(elements)}")
                    review_elements.extend(elements)
                except Exception as e:
                    self.logger.warning(f"   ⚠️ Ошибка селектора {selector}: {e}")
                    continue
            
            self.logger.info(f"   📊 Всего найдено отзывов: {len(review_elements)}")
            
            if not review_elements:
                self.logger.info("   ℹ️ Отзывы не найдены")
                return reviews
            
            # Ограничиваем до первых 10 отзывов
            review_elements = review_elements[:10]
            self.logger.info(f"   🔄 Обработка первых {len(review_elements)} отзывов...")
            
            for i, elem in enumerate(review_elements, 1):
                try:
                    self.logger.info(f"   📝 Отзыв {i}/{len(review_elements)} - обработка...")
                    
                    # Автор
                    author_selectors = [
                        ".//span[contains(@class, 'business-review-view__author')]",
                        ".//span[contains(@class, 'review-author')]",
                        ".//div[contains(@class, 'author')]"
                    ]
                    
                    author = ""
                    for author_selector in author_selectors:
                        try:
                            author_elem = elem.find_element(By.XPATH, author_selector)
                            author = author_elem.text.strip()
                            if author:
                                break
                        except:
                            continue
                    
                    # Рейтинг
                    rating_selectors = [
                        ".//div[contains(@class, 'business-rating-badge-view__rating')]",
                        ".//div[contains(@class, 'rating')]",
                        ".//span[contains(@class, 'rating')]"
                    ]
                    
                    rating = ""
                    for rating_selector in rating_selectors:
                        try:
                            rating_elem = elem.find_element(By.XPATH, rating_selector)
                            rating = rating_elem.text.strip()
                            if rating:
                                break
                        except:
                            continue
                    
                    # Текст отзыва
                    text_selectors = [
                        ".//span[contains(@class, 'business-review-view__body-text')]",
                        ".//div[contains(@class, 'review-text')]",
                        ".//p"
                    ]
                    
                    text = ""
                    for text_selector in text_selectors:
                        try:
                            text_elem = elem.find_element(By.XPATH, text_selector)
                            text = text_elem.text.strip()
                            if text:
                                break
                        except:
                            continue
                    
                    # Дата
                    date_selectors = [
                        ".//span[contains(@class, 'business-review-view__date')]",
                        ".//div[contains(@class, 'review-date')]",
                        ".//span[contains(@class, 'date')]"
                    ]
                    
                    date = ""
                    for date_selector in date_selectors:
                        try:
                            date_elem = elem.find_element(By.XPATH, date_selector)
                            date = date_elem.text.strip()
                            if date:
                                break
                        except:
                            continue
                    
                    if author or text:
                        review_data = {
                            'author': author,
                            'rating': rating,
                            'text': text,
                            'date': date
                        }
                        reviews.append(review_data)
                        self.logger.info(f"   ✅ Отзыв {i}: от {author}")
                    else:
                        self.logger.warning(f"   ⚠️ Отзыв {i}: данные не найдены")
                        
                except Exception as e:
                    self.logger.error(f"   ❌ Ошибка обработки отзыва {i}: {e}")
                    continue
            
            self.logger.info(f"✅ Извлечено отзывов: {len(reviews)}")
            return reviews
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения отзывов: {e}")
            return []
    
    def extract_branches(self):
        """Извлечение информации о филиалах"""
        branches = []
        
        try:
            self.logger.info("🏪 Извлечение информации о филиалах...")
            
            # Переход на вкладку филиалов
            self.logger.info("   🔄 Попытка перехода на вкладку филиалов...")
            if self.navigate_to_tab('chain'):
                time.sleep(3)
                self.logger.info("   ✅ Переход на вкладку филиалов выполнен")
            else:
                self.logger.warning("   ⚠️ Не удалось перейти на вкладку филиалов")
                return branches
            
            # Поиск филиалов с множественными селекторами
            branch_selectors = [
                "//div[contains(@class, 'search-snippet-view')]",
                "//div[contains(@class, 'branch-item')]",
                "//div[contains(@class, 'chain-item')]"
            ]
            
            self.logger.info("   🔍 Поиск элементов филиалов...")
            branch_elements = []
            for j, selector in enumerate(branch_selectors, 1):
                try:
                    self.logger.info(f"   📍 Селектор {j}/{len(branch_selectors)}: {selector}")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    self.logger.info(f"   🏪 Найдено филиалов: {len(elements)}")
                    branch_elements.extend(elements)
                except Exception as e:
                    self.logger.warning(f"   ⚠️ Ошибка селектора {selector}: {e}")
                    continue
            
            self.logger.info(f"   📊 Всего найдено филиалов: {len(branch_elements)}")
            
            if not branch_elements:
                self.logger.info("   ℹ️ Филиалы не найдены")
                return branches
            
            self.logger.info("   🔄 Обработка найденных филиалов...")
            for i, elem in enumerate(branch_elements, 1):
                try:
                    self.logger.info(f"   🏪 Филиал {i}/{len(branch_elements)} - обработка...")
                    
                    # Название филиала
                    name_selectors = [
                        ".//div[contains(@class, 'search-snippet-view__title')]",
                        ".//div[contains(@class, 'branch-title')]",
                        ".//h3",
                        ".//h4"
                    ]
                    
                    name = ""
                    for name_selector in name_selectors:
                        try:
                            name_elem = elem.find_element(By.XPATH, name_selector)
                            name = name_elem.text.strip()
                            if name:
                                break
                        except:
                            continue
                    
                    # Адрес филиала
                    addr_selectors = [
                        ".//div[contains(@class, 'search-snippet-view__address')]",
                        ".//div[contains(@class, 'branch-address')]",
                        ".//div[contains(@class, 'address')]"
                    ]
                    
                    address = ""
                    for addr_selector in addr_selectors:
                        try:
                            addr_elem = elem.find_element(By.XPATH, addr_selector)
                            address = addr_elem.text.strip()
                            if address:
                                break
                        except:
                            continue
                    
                    if name or address:
                        branch_data = {
                            'name': name,
                            'address': address
                        }
                        branches.append(branch_data)
                        self.logger.info(f"   ✅ Филиал {i}: {name}")
                    else:
                        self.logger.warning(f"   ⚠️ Филиал {i}: данные не найдены")
                        
                except Exception as e:
                    self.logger.error(f"   ❌ Ошибка обработки филиала {i}: {e}")
                    continue
            
            self.logger.info(f"✅ Извлечено филиалов: {len(branches)}")
            return branches
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения филиалов: {e}")
            return []
    
    def extract_comprehensive_data(self, business_url):
        """Комплексное извлечение всех данных с одной карточки"""
        try:
            self.logger.info(f"\n🔍 ОБРАБОТКА: {business_url}")
            
            # Переход к карточке предприятия
            self.logger.info("📄 Загрузка страницы предприятия...")
            self.driver.get(business_url)
            time.sleep(3)
            self.logger.info("✅ Страница предприятия загружена")
            
            # Сбор всех данных
            data = {
                'url': business_url,
                'extraction_date': datetime.now().isoformat(),
                'yandex_id': self.extract_yandex_id(business_url)
            }
            
            # Прогресс-бар для этапов извлечения
            stages = [
                ("📝 Базовая информация", self.extract_basic_info),
                ("📞 Контактная информация", self.extract_contact_info),
                ("🔧 Особенности и услуги", self.extract_features_and_services),
                ("🖼️ Медиа-контент", self.extract_media_content),
                ("🛍️ Товары и услуги", self.extract_products_and_services),
                ("⭐ Отзывы", self.extract_reviews),
                ("🏪 Филиалы", self.extract_branches)
            ]
            
            for i, (stage_name, stage_func) in enumerate(stages, 1):
                self.logger.info(f"\n🔄 ЭТАП {i}/{len(stages)}: {stage_name}")
                self.logger.info("=" * 50)
                
                try:
                    if stage_name == "🛍️ Товары и услуги":
                        result = stage_func()
                        data['products_and_services'] = result
                    elif stage_name == "⭐ Отзывы":
                        result = stage_func()
                        data['reviews'] = result
                    elif stage_name == "🏪 Филиалы":
                        result = stage_func()
                        data['branches'] = result
                    else:
                        result = stage_func()
                        data.update(result)
                    
                    self.logger.info(f"✅ {stage_name} - ЗАВЕРШЕН")
                    
                except Exception as e:
                    self.logger.error(f"❌ Ошибка на этапе {stage_name}: {e}")
                    if stage_name == "🛍️ Товары и услуги":
                        data['products_and_services'] = []
                    elif stage_name == "⭐ Отзывы":
                        data['reviews'] = []
                    elif stage_name == "🏪 Филиалы":
                        data['branches'] = []
                    else:
                        # Для остальных этапов добавляем пустые данные
                        pass
            
            if data.get('name'):
                self.logger.info(f"   ✅ {data['name']} - данные собраны успешно")
                return data
            else:
                self.logger.warning(f"   ❌ Данные не извлечены")
                return None
                
        except Exception as e:
            self.logger.error(f"   ❌ Ошибка обработки {business_url}: {e}")
            return None
    
    def extract_yandex_id(self, url):
        """Извлечение Yandex ID из URL"""
        try:
            match = re.search(r'/org/.+?/(\d+)/', url)
            return match.group(1) if match else ""
        except:
            return ""
    
    def find_element_by_selectors(self, selectors):
        """Поиск элемента по списку селекторов"""
        for selector in selectors:
            try:
                if '/@' in selector:  # Атрибут
                    xpath_parts = selector.split('/@')
                    element = self.driver.find_element(By.XPATH, xpath_parts[0])
                    return element
                else:
                    return self.driver.find_element(By.XPATH, selector)
            except:
                continue
        return None
    
    def extract_by_selectors(self, selectors):
        """Извлечение текста по списку селекторов"""
        for selector in selectors:
            try:
                if '/@' in selector:  # Атрибут
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
    
    def save_results(self, filename_prefix="comprehensive_data"):
        """Сохранение результатов в JSON и CSV"""
        try:
            os.makedirs("output", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # JSON
            json_filename = f"output/{filename_prefix}_{timestamp}.json"
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(self.businesses, f, ensure_ascii=False, indent=2)
            
            # CSV
            csv_filename = f"output/{filename_prefix}_{timestamp}.csv"
            self.save_to_csv(csv_filename)
            
            self.logger.info(f"💾 Результаты сохранены:")
            self.logger.info(f"   📄 JSON: {json_filename}")
            self.logger.info(f"   📊 CSV: {csv_filename}")
            self.logger.info(f"   📊 Обработано предприятий: {len(self.businesses)}")
            
            return json_filename, csv_filename
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения: {e}")
            return None, None
    
    def save_to_csv(self, filename):
        """Сохранение данных в CSV таблицу"""
        try:
            if not self.businesses:
                self.logger.warning("⚠️ Нет данных для сохранения в CSV")
                return
            
            # Определяем все возможные поля
            all_fields = set()
            for business in self.businesses:
                all_fields.update(self.flatten_dict(business).keys())
            
            # Сортируем поля для стабильного порядка
            fieldnames = sorted(list(all_fields))
            self.logger.info(f"📊 Создание CSV с {len(fieldnames)} полями")
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for business in self.businesses:
                    # Преобразуем вложенные структуры в плоский формат
                    flat_business = self.flatten_dict(business)
                    writer.writerow(flat_business)
            
            self.logger.info(f"✅ CSV файл создан: {filename}")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения CSV: {e}")
    
    def flatten_dict(self, d, parent_key='', sep='_'):
        """Преобразование вложенного словаря в плоский"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Преобразуем списки в строки
                if v and isinstance(v[0], dict):
                    # Список словарей (например, отзывы)
                    items.append((new_key, f"{len(v)} items"))
                else:
                    # Простой список
                    items.append((new_key, '; '.join(map(str, v))))
            else:
                items.append((new_key, v))
        return dict(items)
    
    def parse(self, search_url):
        """Основной метод парсинга"""
        self.logger.info("🚀 ЗАПУСК КОМПЛЕКСНОГО ПАРСЕРА ЯНДЕКС КАРТ")
        self.logger.info("=" * 60)
        
        try:
            # Инициализация
            if not self.setup_driver():
                return False
            
            # Переход к странице поиска
            if not self.navigate_to_search(search_url):
                return False
            
            # Сбор URL предприятий
            business_urls = self.collect_all_business_urls()
            if not business_urls:
                self.logger.error("❌ Не найдено предприятий для обработки")
                return False
            
            self.logger.info(f"\n📋 К ОБРАБОТКЕ: {len(business_urls)} предприятий")
            
            # Обработка каждого предприятия
            for i, business_url in enumerate(business_urls, 1):
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"📍 ПРЕДПРИЯТИЕ {i}/{len(business_urls)}")
                self.logger.info(f"{'='*60}")
                
                if business_url in self.processed_urls:
                    self.logger.warning(f"   ⚠️ Уже обработано: {business_url}")
                    continue
                
                start_time = time.time()
                data = self.extract_comprehensive_data(business_url)
                end_time = time.time()
                
                if data:
                    self.businesses.append(data)
                    self.processed_urls.add(business_url)
                    self.logger.info(f"✅ Предприятие {i} обработано за {end_time - start_time:.1f} сек")
                else:
                    self.logger.error(f"❌ Предприятие {i} не удалось обработать")
                
                # Пауза между запросами
                if i < len(business_urls):
                    self.logger.info("⏳ Пауза 2 секунды перед следующим предприятием...")
                    time.sleep(2)
            
            # Сохранение результатов
            self.save_results()
            
            self.logger.info(f"\n🎉 ПАРСИНГ ЗАВЕРШЕН")
            self.logger.info(f"✅ Успешно обработано: {len(self.businesses)} предприятий")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка: {e}")
            return False
        
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("🔚 WebDriver закрыт")


def main():
    """Точка входа"""
    # URL для парсинга
    search_url = "https://yandex.ru/maps/39/rostov-na-donu/search/Ростов%20на%20дону%20суворовский%20стоматология/?ll=39.806284%2C47.275656&sctx=ZAAAAAgCEAAaKAoSCbnEkQci10NAESl4CrlSn0dAEhIJ98ySADW1zj8R1lJA2v8Aqz8iBgABAgMEBSgKOABA0YgGSAFqAnJ1nQHNzMw9oAEAqAEAvQHFGEBwwgElzKy6tfoGxpeW5AXL5fTcA9Ka8PoDwpzMogT4sL%2FgA%2Fyw57rlBoICStCg0L7RgdGC0L7QsiDQvdCwINC00L7QvdGDINGB0YPQstC%2B0YDQvtCy0YHQutC40Lkg0YHRgtC%2B0LzQsNGC0L7Qu9C%2B0LPQuNGPigIAkgICMzmaAgxkZXNrdG9wLW1hcHPaAigKEgnfWbvtQuFDQBGw%2Fs8gd6FHQBISCYBnXaPlQN0%2FEQA8uDtrt7k%2F4AIB&sll=39.806284%2C47.275656&sspn=0.914172%2C0.200856&z=10.61"
    
    # Количество предприятий для сбора
    target_count = 3
    
    parser = YandexMapsComprehensiveParser(target_count=target_count)
    parser.parse(search_url)


if __name__ == "__main__":
    main()
