#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Чистый парсер Яндекс Карт на основе реальной структуры
"""

import time
import os
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class CleanYandexMapsParser:
    """Простой и рабочий парсер Яндекс Карт"""
    
    def __init__(self):
        self.driver = None
        self.businesses = []
    
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
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(10)
            print("✅ Браузер запущен")
            return True
        except Exception as e:
            print(f"❌ Ошибка запуска браузера: {e}")
            return False
    
    def navigate_to_search(self, url):
        """Переход на страницу поиска"""
        print(f"📖 Переход на: {url}")
        try:
            self.driver.get(url)
            time.sleep(5)
            print("✅ Страница загружена")
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки страницы: {e}")
            return False
    
    def get_search_results(self):
        """Получение списка результатов поиска"""
        print("🔍 Поиск результатов...")
        
        # Прокрутка для загрузки результатов
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # Поиск элементов списка
        selectors = [
            "//div[contains(@class, 'search-snippet-view')]",
            "//li[contains(@class, 'serp-item')]", 
            "//div[contains(@class, 'business-snippet-view')]"
        ]
        
        results = []
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    results = elements
                    print(f"✅ Найдено {len(elements)} результатов")
                    break
            except:
                continue
        
        return results
    
    def click_and_extract(self, result_element, index):
        """Клик по результату и извлечение данных"""
        print(f"🎯 Обработка результата {index + 1}")
        
        business_data = {
            'name': '',
            'address': '',
            'phone': '',
            'rating': '',
            'reviews_count': '',
            'website': '',
            'working_hours': '',
            'categories': [],
            'services': '',
            'social_links': []
        }
        
        try:
            # Попытка найти и кликнуть по названию
            clickable_selectors = [
                ".//span[contains(@class, 'search-business-snippet-view__title')]",
                ".//a", 
                ".//div[contains(@class, 'title')]"
            ]
            
            clicked = False
            for selector in clickable_selectors:
                try:
                    clickable = result_element.find_element(By.XPATH, selector)
                    if clickable.is_displayed():
                        clickable.click()
                        clicked = True
                        print("🖱️ Клик выполнен")
                        break
                except:
                    continue
            
            if not clicked:
                # Клик по самому элементу
                result_element.click()
                print("🖱️ Клик по элементу выполнен")
            
            # Ожидание загрузки карточки
            time.sleep(4)
            
            # Проверка появления карточки
            card_loaded = False
            card_selectors = [
                "//div[contains(@class, 'business-card-view__main-wrapper')]",
                "//h1[contains(@class, 'card-title-view__title')]"
            ]
            
            for selector in card_selectors:
                try:
                    if self.driver.find_element(By.XPATH, selector).is_displayed():
                        card_loaded = True
                        print("✅ Карточка загружена")
                        break
                except:
                    continue
            
            if card_loaded:
                # Извлечение данных из карточки
                business_data = self.extract_business_card_data()
            else:
                print("⚠️ Карточка не загрузилась, извлекаем базовые данные")
                business_data = self.extract_snippet_data(result_element)
            
            # Возврат к списку
            self.return_to_list()
            
            return business_data
            
        except Exception as e:
            print(f"❌ Ошибка обработки результата: {e}")
            self.return_to_list()
            return business_data
    
    def extract_business_card_data(self):
        """Извлечение данных из полной карточки предприятия"""
        data = {
            'name': '',
            'address': '',
            'phone': '',
            'rating': '',
            'reviews_count': '',
            'website': '',
            'working_hours': '',
            'categories': [],
            'services': '',
            'social_links': []
        }
        
        try:
            # Название
            try:
                name_elem = self.driver.find_element(By.XPATH, "//h1[contains(@class, 'card-title-view__title')]//a")
                data['name'] = name_elem.text.strip()
            except:
                try:
                    name_elem = self.driver.find_element(By.XPATH, "//h1[contains(@class, 'card-title-view__title')]")
                    data['name'] = name_elem.text.strip()
                except:
                    pass
            
            # Адрес
            try:
                address_elem = self.driver.find_element(By.XPATH, "//div[contains(@class, 'business-contacts-view__address-link')]")
                data['address'] = address_elem.text.strip()
            except:
                pass
            
            # Телефон
            try:
                phone_elem = self.driver.find_element(By.XPATH, "//span[@itemprop='telephone']")
                data['phone'] = phone_elem.text.strip()
            except:
                pass
            
            # Рейтинг
            try:
                rating_elem = self.driver.find_element(By.XPATH, "//span[contains(@class, 'business-rating-badge-view__rating-text')]")
                data['rating'] = rating_elem.text.strip()
            except:
                pass
            
            # Количество отзывов
            try:
                reviews_elem = self.driver.find_element(By.XPATH, "//div[contains(@class, 'business-header-rating-view__text')]")
                data['reviews_count'] = reviews_elem.text.strip()
            except:
                pass
            
            # Веб-сайт
            try:
                website_elem = self.driver.find_element(By.XPATH, "//a[@itemprop='url']")
                data['website'] = website_elem.get_attribute('href')
            except:
                pass
            
            # Время работы
            try:
                hours_elem = self.driver.find_element(By.XPATH, "//div[contains(@class, 'business-card-working-status-view__text')]")
                data['working_hours'] = hours_elem.text.strip()
            except:
                pass
            
            # Категории
            try:
                category_elements = self.driver.find_elements(By.XPATH, "//a[contains(@class, 'business-categories-view__category')]")
                data['categories'] = [elem.text.strip() for elem in category_elements if elem.text.strip()]
            except:
                pass
            
            # Услуги
            try:
                services_elem = self.driver.find_element(By.XPATH, "//span[contains(@class, 'business-features-view__valued-value')]")
                data['services'] = services_elem.text.strip()
            except:
                pass
            
            # Социальные сети
            try:
                social_elements = self.driver.find_elements(By.XPATH, "//a[@itemprop='sameAs']")
                data['social_links'] = [elem.get_attribute('href') for elem in social_elements]
            except:
                pass
            
        except Exception as e:
            print(f"❌ Ошибка извлечения данных карточки: {e}")
        
        return data
    
    def extract_snippet_data(self, element):
        """Извлечение базовых данных из сниппета"""
        data = {
            'name': '',
            'address': '',
            'phone': '',
            'rating': '',
            'reviews_count': '',
            'website': '',
            'working_hours': '',
            'categories': [],
            'services': '',
            'social_links': []
        }
        
        try:
            # Название из сниппета
            name_selectors = [
                ".//span[contains(@class, 'search-business-snippet-view__title')]",
                ".//div[contains(@class, 'title')]"
            ]
            for selector in name_selectors:
                try:
                    name_elem = element.find_element(By.XPATH, selector)
                    data['name'] = name_elem.text.strip()
                    break
                except:
                    continue
            
            # Адрес из сниппета
            address_selectors = [
                ".//span[contains(@class, 'search-business-snippet-view__address')]",
                ".//div[contains(@class, 'address')]"
            ]
            for selector in address_selectors:
                try:
                    addr_elem = element.find_element(By.XPATH, selector)
                    data['address'] = addr_elem.text.strip()
                    break
                except:
                    continue
                    
        except Exception as e:
            print(f"❌ Ошибка извлечения данных сниппета: {e}")
        
        return data
    
    def return_to_list(self):
        """Возврат к списку результатов"""
        try:
            # Попытка нажать ESC
            from selenium.webdriver.common.keys import Keys
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(2)
        except:
            try:
                # Возврат назад
                self.driver.back()
                time.sleep(3)
            except:
                pass
    
    def parse(self, url, max_results=10):
        """Основной метод парсинга"""
        print("🚀 Запуск парсинга Яндекс Карт")
        print("=" * 50)
        
        if not self.setup_driver():
            return False
        
        if not self.navigate_to_search(url):
            return False
        
        # Получение результатов поиска
        results = self.get_search_results()
        if not results:
            print("❌ Результаты поиска не найдены")
            return False
        
        # Ограничение количества результатов
        results = results[:max_results]
        print(f"📊 Обработка {len(results)} результатов")
        
        # Обработка каждого результата
        for i, result in enumerate(results):
            business_data = self.click_and_extract(result, i)
            if business_data['name']:
                self.businesses.append(business_data)
                print(f"✅ {i+1}. {business_data['name']}")
            else:
                print(f"⚠️ {i+1}. Данные не извлечены")
            
            time.sleep(2)  # Пауза между обработкой
        
        print(f"\n📈 Парсинг завершен: {len(self.businesses)} предприятий")
        return True
    
    def save_results(self):
        """Сохранение результатов в Excel"""
        if not self.businesses:
            print("❌ Нет данных для сохранения")
            return
        
        # Создание папки output
        os.makedirs("output", exist_ok=True)
        
        # Подготовка данных для DataFrame
        data_for_df = []
        for business in self.businesses:
            row = {
                'Название': business['name'],
                'Адрес': business['address'],
                'Телефон': business['phone'],
                'Рейтинг': business['rating'],
                'Отзывы': business['reviews_count'],
                'Сайт': business['website'],
                'Время работы': business['working_hours'],
                'Категории': ', '.join(business['categories']),
                'Услуги': business['services'],
                'Соцсети': ', '.join(business['social_links'])
            }
            data_for_df.append(row)
        
        # Сохранение в Excel
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/yandex_maps_{timestamp}.xlsx"
        
        df = pd.DataFrame(data_for_df)
        df.to_excel(filename, index=False)
        
        print(f"💾 Результаты сохранены: {filename}")
        print(f"📊 Всего записей: {len(data_for_df)}")
    
    def close(self):
        """Закрытие браузера"""
        if self.driver:
            self.driver.quit()
            print("🔚 Браузер закрыт")

def main():
    """Основная функция"""
    parser = CleanYandexMapsParser()
    
    try:
        # URL для парсинга
        url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/"
        
        # Парсинг
        if parser.parse(url, max_results=5):  # Ограничиваем 5 результатами для теста
            parser.save_results()
        
        print("\n👀 Браузер оставлен открытым для анализа")
        print("Нажмите Enter для закрытия...")
        input()
        
    except KeyboardInterrupt:
        print("\n⏹️ Парсинг остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        parser.close()

if __name__ == "__main__":
    main()
