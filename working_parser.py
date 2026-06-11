#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Рабочий парсер для Яндекс Карт - работает с маркерами карты
"""

import os
import time
import logging
from datetime import datetime
from config import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import json

class WorkingYandexMapsParser:
    def __init__(self):
        self.driver = None
        self.setup_logging()
        
    def setup_logging(self):
        """Настройка логирования"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('working_parser.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_driver(self):
        """Настройка драйвера"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(10)
            self.logger.info("✅ WebDriver запущен")
            return True
        except Exception as e:
            self.logger.error(f"❌ Ошибка запуска WebDriver: {e}")
            return False
    
    def get_business_markers(self):
        """Получение всех маркеров предприятий с карты"""
        self.logger.info("🔍 Загрузка страницы поиска...")
        self.driver.get(SEARCH_URL)
        time.sleep(8)
        
        # Сохранение HTML для отладки
        with open('working_debug.html', 'w', encoding='utf-8') as f:
            f.write(self.driver.page_source)
        
        business_data = []
        processed_ids = set()
        
        # Прокрутка карты и сбор маркеров
        for scroll_round in range(5):
            self.logger.info(f"📜 Раунд прокрутки {scroll_round + 1}")
            
            # Поиск всех маркеров на карте
            markers = self.driver.find_elements(By.XPATH, "//div[@class='search-placemark-view'][@data-id]")
            self.logger.info(f"🔍 Найдено маркеров: {len(markers)}")
            
            new_markers = 0
            for marker in markers:
                try:
                    data_id = marker.get_attribute('data-id')
                    if data_id and data_id not in processed_ids:
                        processed_ids.add(data_id)
                        new_markers += 1
                        
                        # Клик по маркеру
                        self.logger.info(f"🖱️ Клик по маркеру {data_id}")
                        self.driver.execute_script("arguments[0].click();", marker)
                        time.sleep(3)
                        
                        # Извлечение данных
                        business_info = self.extract_business_info(data_id)
                        if business_info:
                            business_data.append(business_info)
                            self.logger.info(f"✅ Добавлено предприятие: {business_info.get('name', 'Без названия')}")
                        
                        # Проверка достижения лимита
                        if TARGET_BUSINESSES_COUNT > 0 and len(business_data) >= TARGET_BUSINESSES_COUNT:
                            self.logger.info(f"🎯 Достигнут лимит: {TARGET_BUSINESSES_COUNT}")
                            return business_data
                            
                except Exception as e:
                    self.logger.debug(f"❌ Ошибка обработки маркера: {e}")
                    continue
            
            self.logger.info(f"📊 Новых маркеров в раунде: {new_markers}")
            
            # Прокрутка для загрузки новых маркеров
            self.scroll_map()
            time.sleep(3)
            
            # Если нет новых маркеров, пробуем увеличить масштаб
            if new_markers == 0:
                self.logger.info("🔍 Попытка изменения масштаба...")
                self.driver.execute_script("window.dispatchEvent(new WheelEvent('wheel', {deltaY: -500}));")
                time.sleep(3)
        
        return business_data
    
    def scroll_map(self):
        """Прокрутка карты для загрузки новых маркеров"""
        try:
            # Прокрутка в разных направлениях
            map_container = self.driver.find_element(By.CLASS_NAME, "map-container")
            
            # Прокрутка вниз
            self.driver.execute_script("arguments[0].scrollTop += 500;", map_container)
            time.sleep(1)
            
            # Прокрутка вправо
            self.driver.execute_script("arguments[0].scrollLeft += 500;", map_container)
            time.sleep(1)
            
            # Общая прокрутка страницы
            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(1)
            
        except Exception as e:
            self.logger.debug(f"❌ Ошибка прокрутки: {e}")
    
    def extract_business_info(self, data_id):
        """Извлечение информации о предприятии"""
        try:
            business_info = {
                'id': data_id,
                'name': 'N/A',
                'address': 'N/A', 
                'phone': 'N/A',
                'rating': 'N/A',
                'url': 'N/A',
                'website': 'N/A',
                'working_hours': 'N/A',
                'products_and_services': []
            }
            
            # Ждем загрузки карточки
            time.sleep(2)
            
            # Название
            try:
                name_selectors = [
                    "//h1[contains(@class, 'card-title-view__title')]",
                    "//div[contains(@class, 'card-title-view__title')]",
                    "//h1[contains(@class, 'orgpage-header-view__title')]",
                    "//div[contains(@class, 'business-card-title')]"
                ]
                
                for selector in name_selectors:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        business_info['name'] = elements[0].text.strip()
                        break
            except:
                pass
            
            # Адрес
            try:
                address_selectors = [
                    "//div[contains(@class, 'card-title-view__description')]",
                    "//div[contains(@class, 'business-contact-view__address')]",
                    "//span[contains(@class, 'business-contacts-view__address')]"
                ]
                
                for selector in address_selectors:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        business_info['address'] = elements[0].text.strip()
                        break
            except:
                pass
            
            # Телефон
            try:
                phone_selectors = [
                    "//div[contains(@class, 'business-contacts-view__phone')]",
                    "//a[contains(@href, 'tel:')]",
                    "//span[contains(@class, 'phone')]"
                ]
                
                for selector in phone_selectors:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        business_info['phone'] = elements[0].text.strip()
                        break
            except:
                pass
            
            # Рейтинг
            try:
                rating_selectors = [
                    "//div[contains(@class, 'business-rating-badge-view__rating')]",
                    "//span[contains(@class, 'rating')]"
                ]
                
                for selector in rating_selectors:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    if elements:
                        business_info['rating'] = elements[0].text.strip()
                        break
            except:
                pass
            
            # URL текущей страницы
            business_info['url'] = self.driver.current_url
            
            # Веб-сайт
            try:
                website_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'http') and not(contains(@href, 'yandex'))]")
                if website_elements:
                    business_info['website'] = website_elements[0].get_attribute('href')
            except:
                pass
            
            # Часы работы
            try:
                hours_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'business-schedule-view')]")
                if hours_elements:
                    business_info['working_hours'] = hours_elements[0].text.strip()
            except:
                pass
            
            # Товары и услуги - пробуем найти вкладку товаров
            try:
                # Поиск вкладки "Товары" или "Услуги"
                tabs = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'tabs-select-view__tab')]")
                for tab in tabs:
                    if any(word in tab.text.lower() for word in ['товар', 'услуг', 'цен', 'прайс']):
                        self.driver.execute_script("arguments[0].click();", tab)
                        time.sleep(3)
                        
                        # Извлечение товаров/услуг
                        product_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'related-item-list-view__item')]")
                        for elem in product_elements[:TARGET_PRODUCTS_COUNT]:
                            try:
                                product_name = elem.find_element(By.XPATH, ".//div[contains(@class, 'title')]").text.strip()
                                try:
                                    product_price = elem.find_element(By.XPATH, ".//div[contains(@class, 'price')]").text.strip()
                                except:
                                    product_price = 'Цена не указана'
                                
                                business_info['products_and_services'].append({
                                    'name': product_name,
                                    'price': product_price
                                })
                            except:
                                continue
                        break
            except:
                pass
            
            return business_info
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения данных для {data_id}: {e}")
            return None
    
    def save_results(self, business_data):
        """Сохранение результатов"""
        if not business_data:
            self.logger.warning("⚠️ Нет данных для сохранения")
            return
        
        # Создание папки результатов
        os.makedirs(FOLDER_STRUCTURE['base_folder'], exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Сохранение JSON
        json_file = f"{FOLDER_STRUCTURE['base_folder']}/working_results_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(business_data, f, ensure_ascii=False, indent=2)
        
        # Сохранение CSV
        csv_file = f"{FOLDER_STRUCTURE['base_folder']}/working_results_{timestamp}.csv"
        with open(csv_file, 'w', encoding='utf-8', newline='') as f:
            import csv
            writer = csv.writer(f)
            writer.writerow(['ID', 'Название', 'Адрес', 'Телефон', 'Рейтинг', 'URL', 'Сайт', 'Часы работы', 'Товары/Услуги'])
            
            for business in business_data:
                products_str = '; '.join([f"{p.get('name', '')}: {p.get('price', '')}" for p in business.get('products_and_services', [])])
                writer.writerow([
                    business.get('id', ''),
                    business.get('name', ''),
                    business.get('address', ''),
                    business.get('phone', ''),
                    business.get('rating', ''),
                    business.get('url', ''),
                    business.get('website', ''),
                    business.get('working_hours', ''),
                    products_str
                ])
        
        # Сводка
        summary_file = f"{FOLDER_STRUCTURE['base_folder']}/working_summary_{timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("СВОДКА РАБОЧЕГО ПАРСЕРА\n")
            f.write("="*80 + "\n")
            f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"URL поиска: {SEARCH_URL}\n")
            f.write(f"Найдено предприятий: {len(business_data)}\n\n")
            
            for i, business in enumerate(business_data, 1):
                f.write(f"{i}. {business.get('name', 'N/A')}\n")
                f.write(f"   ID: {business.get('id', 'N/A')}\n")
                f.write(f"   Адрес: {business.get('address', 'N/A')}\n")
                f.write(f"   Телефон: {business.get('phone', 'N/A')}\n")
                f.write(f"   Рейтинг: {business.get('rating', 'N/A')}\n")
                f.write(f"   Товары/услуги: {len(business.get('products_and_services', []))}\n\n")
        
        self.logger.info(f"💾 Результаты сохранены:")
        self.logger.info(f"   📄 JSON: {json_file}")
        self.logger.info(f"   📊 CSV: {csv_file}")
        self.logger.info(f"   📋 Сводка: {summary_file}")
    
    def run(self):
        """Основной метод запуска"""
        try:
            self.logger.info("🚀 ЗАПУСК РАБОЧЕГО ПАРСЕРА")
            self.logger.info("="*60)
            
            if not self.setup_driver():
                return False
            
            # Получение данных предприятий
            business_data = self.get_business_markers()
            
            self.logger.info(f"📊 Найдено предприятий: {len(business_data)}")
            
            # Сохранение результатов
            self.save_results(business_data)
            
            self.logger.info("🎉 ПАРСИНГ ЗАВЕРШЕН УСПЕШНО!")
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
    print("🚀 ЗАПУСК РАБОЧЕГО ПАРСЕРА YANDEX MAPS")
    print("="*60)
    print(f"📄 URL поиска: {SEARCH_URL}")
    print(f"🎯 Целевое количество предприятий: {TARGET_BUSINESSES_COUNT}")
    print(f"🛍️ Целевое количество товаров: {TARGET_PRODUCTS_COUNT}")
    print("="*60)
    
    parser = WorkingYandexMapsParser()
    success = parser.run()
    
    if success:
        print("\n✅ Парсинг завершен успешно!")
        print(f"📁 Результаты сохранены в папке: {FOLDER_STRUCTURE['base_folder']}")
    else:
        print("\n❌ Парсинг завершен с ошибками!")

if __name__ == "__main__":
    main()
