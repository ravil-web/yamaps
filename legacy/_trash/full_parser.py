#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Полный парсер Яндекс Карт - собирает ВСЮ информацию из карточки предприятия
Основан на реальной структуре карточки предприятия
"""

import time
import os
import pandas as pd
import json
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys

class FullYandexMapsParser:
    """Полный парсер Яндекс Карт с извлечением всех данных"""
    
    def __init__(self):
        self.driver = None
        self.businesses = []
        self.wait = None
    
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
            self.wait = WebDriverWait(self.driver, 10)
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
            
            # Прокрутка для загрузки результатов
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            print("✅ Страница загружена")
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки страницы: {e}")
            return False
    
    def get_search_results(self):
        """Получение списка результатов поиска"""
        print("🔍 Поиск результатов...")
        
        selectors = [
            "//div[contains(@class, 'search-snippet-view')]",
            "//li[contains(@class, 'serp-item')]", 
            "//div[contains(@class, 'business-snippet-view')]",
            "//div[contains(@class, 'search-business-snippet-view')]"
        ]
        
        results = []
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    results = elements
                    print(f"✅ Найдено {len(elements)} результатов с селектором: {selector}")
                    break
            except:
                continue
        
        return results
    
    def click_business(self, result_element, index):
        """Клик по предприятию и переход к карточке"""
        print(f"🎯 Клик по предприятию {index + 1}")
        
        try:
            # Различные способы клика
            clickable_selectors = [
                ".//span[contains(@class, 'search-business-snippet-view__title')]",
                ".//a[contains(@class, 'search-snippet-view__title')]",
                ".//div[contains(@class, 'search-snippet-view__title')]",
                ".//span[contains(@class, 'business-snippet-view__name')]",
                "."  # сам элемент
            ]
            
            clicked = False
            for selector in clickable_selectors:
                try:
                    if selector == ".":
                        clickable = result_element
                    else:
                        clickable = result_element.find_element(By.XPATH, selector)
                    
                    if clickable.is_displayed():
                        self.driver.execute_script("arguments[0].click();", clickable)
                        clicked = True
                        print("🖱️ Клик выполнен")
                        break
                except:
                    continue
            
            if not clicked:
                print("⚠️ Клик не удался")
                return False
            
            # Ожидание загрузки карточки
            time.sleep(4)
            
            # Проверка появления карточки
            card_selectors = [
                "//div[contains(@class, 'business-card-view__main-wrapper')]",
                "//h1[contains(@class, 'card-title-view__title')]"
            ]
            
            for selector in card_selectors:
                try:
                    if self.driver.find_element(By.XPATH, selector).is_displayed():
                        print("✅ Карточка предприятия загружена")
                        return True
                except:
                    continue
            
            print("⚠️ Карточка не загрузилась")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка клика: {e}")
            return False
    
    def extract_full_business_data(self):
        """Извлечение ВСЕХ данных из карточки предприятия"""
        print("📊 Извлечение полных данных...")
        
        data = {
            # Основная информация
            'name': '',
            'verified': False,
            'categories': [],
            'rating': '',
            'reviews_count': '',
            'awards': [],
            
            # Контактная информация
            'address': '',
            'phones': [],
            'website': '',
            'social_links': {
                'whatsapp': '',
                'vk': '',
                'instagram': '',
                'facebook': '',
                'telegram': '',
                'other': []
            },
            
            # Время работы
            'working_hours': {
                'current_status': '',
                'schedule': []
            },
            
            # Услуги и товары
            'services': [],
            'products': [],
            'prices': [],
            'features': [],
            
            # Медиа контент
            'has_panorama': False,
            'photos_count': 0,
            'stories': [],
            
            # Дополнительная информация
            'description': '',
            'metro_stations': [],
            'parking_info': '',
            'coordinates': {'lat': '', 'lon': ''},
            
            # Отзывы и рейтинги
            'detailed_ratings': {},
            'recent_reviews': [],
            
            # Техническая информация
            'yandex_id': '',
            'url': '',
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            # НАЗВАНИЕ И ВЕРИФИКАЦИЯ
            try:
                title_elem = self.driver.find_element(By.XPATH, "//h1[contains(@class, 'card-title-view__title')]")
                data['name'] = self.safe_get_text(title_elem)
                
                # Проверка верификации
                try:
                    verified_elem = self.driver.find_element(By.XPATH, "//span[contains(@class, 'business-verified-badge')]")
                    data['verified'] = True
                except:
                    data['verified'] = False
                    
            except:
                pass
            
            # КАТЕГОРИИ
            try:
                category_elements = self.driver.find_elements(By.XPATH, "//a[contains(@class, 'business-categories-view__category')]")
                data['categories'] = [self.safe_get_text(elem) for elem in category_elements]
            except:
                pass
            
            # РЕЙТИНГ И ОТЗЫВЫ
            try:
                rating_elem = self.driver.find_element(By.XPATH, "//span[contains(@class, 'business-rating-badge-view__rating-text')]")
                data['rating'] = self.safe_get_text(rating_elem)
            except:
                pass
            
            try:
                reviews_elem = self.driver.find_element(By.XPATH, "//div[contains(@class, 'business-header-rating-view__text')]")
                reviews_text = self.safe_get_text(reviews_elem)
                numbers = re.findall(r'\d+', reviews_text)
                if numbers:
                    data['reviews_count'] = numbers[0]
            except:
                pass
            
            # НАГРАДЫ
            try:
                award_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'business-header-awards-view__award-text')]")
                data['awards'] = [self.safe_get_text(elem) for elem in award_elements]
            except:
                pass
            
            # АДРЕС
            try:
                address_elem = self.driver.find_element(By.XPATH, "//div[contains(@class, 'business-contacts-view__address-link')]")
                data['address'] = self.safe_get_text(address_elem)
            except:
                # Альтернативный способ через meta
                try:
                    address_meta = self.driver.find_element(By.XPATH, "//meta[@itemprop='address']")
                    data['address'] = address_meta.get_attribute('content')
                except:
                    pass
            
            # ТЕЛЕФОНЫ
            try:
                phone_elements = self.driver.find_elements(By.XPATH, "//span[@itemprop='telephone']")
                data['phones'] = [self.safe_get_text(elem) for elem in phone_elements if self.safe_get_text(elem)]
                
                # Дополнительные телефоны
                try:
                    more_phones = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'card-phones-view__number')]//span")
                    for phone_elem in more_phones:
                        phone_text = self.safe_get_text(phone_elem)
                        if phone_text and '+' in phone_text and phone_text not in data['phones']:
                            data['phones'].append(phone_text)
                except:
                    pass
            except:
                pass
            
            # ВЕБ-САЙТ
            try:
                website_elem = self.driver.find_element(By.XPATH, "//a[@itemprop='url']")
                data['website'] = website_elem.get_attribute('href')
            except:
                try:
                    website_elem = self.driver.find_element(By.XPATH, "//a[contains(@class, 'business-urls-view__link')]")
                    data['website'] = website_elem.get_attribute('href')
                except:
                    pass
            
            # СОЦИАЛЬНЫЕ СЕТИ
            try:
                social_elements = self.driver.find_elements(By.XPATH, "//a[@itemprop='sameAs']")
                for social_elem in social_elements:
                    href = social_elem.get_attribute('href')
                    if 'whatsapp' in href or 'wa.me' in href:
                        data['social_links']['whatsapp'] = href
                    elif 'vk.com' in href:
                        data['social_links']['vk'] = href
                    elif 'instagram' in href:
                        data['social_links']['instagram'] = href
                    elif 'facebook' in href:
                        data['social_links']['facebook'] = href
                    elif 'telegram' in href or 't.me' in href:
                        data['social_links']['telegram'] = href
                    else:
                        data['social_links']['other'].append(href)
            except:
                pass
            
            # ВРЕМЯ РАБОТЫ
            try:
                status_elem = self.driver.find_element(By.XPATH, "//div[contains(@class, 'business-card-working-status-view__text')]")
                data['working_hours']['current_status'] = self.safe_get_text(status_elem)
                
                # Детальное расписание через meta теги
                try:
                    schedule_metas = self.driver.find_elements(By.XPATH, "//meta[@itemprop='openingHours']")
                    data['working_hours']['schedule'] = [meta.get_attribute('content') for meta in schedule_metas]
                except:
                    pass
            except:
                pass
            
            # УСЛУГИ И ОСОБЕННОСТИ
            try:
                services_elem = self.driver.find_element(By.XPATH, "//span[contains(@class, 'business-features-view__valued-value')]")
                services_text = self.safe_get_text(services_elem)
                if services_text:
                    data['services'] = [s.strip() for s in services_text.split(',')]
            except:
                pass
            
            # ОСОБЕННОСТИ (булевые)
            try:
                feature_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'business-features-view__bool-text')]")
                data['features'] = [self.safe_get_text(elem) for elem in feature_elements]
            except:
                pass
            
            # ТОВАРЫ И ЦЕНЫ
            try:
                product_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'related-item-list-view__title')]")
                data['products'] = [self.safe_get_text(elem) for elem in product_elements]
                
                price_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'related-item-list-view__price')]")
                data['prices'] = [self.safe_get_text(elem) for elem in price_elements]
            except:
                pass
            
            # ПАНОРАМА
            try:
                panorama_elem = self.driver.find_element(By.XPATH, "//button[contains(@class, 'card-media-preview _type_panorama')]")
                data['has_panorama'] = True
            except:
                data['has_panorama'] = False
            
            # КОЛИЧЕСТВО ФОТО
            try:
                photo_counter = self.driver.find_element(By.XPATH, "//div[contains(@class, 'tabs-select-view__counter')]")
                counter_text = self.safe_get_text(photo_counter)
                numbers = re.findall(r'\d+', counter_text)
                if numbers:
                    data['photos_count'] = int(numbers[0])
            except:
                pass
            
            # ИСТОРИИ/АКЦИИ
            try:
                story_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'story-preview__title')]")
                data['stories'] = [self.safe_get_text(elem) for elem in story_elements]
            except:
                pass
            
            # URL ТЕКУЩЕЙ СТРАНИЦЫ
            data['url'] = self.driver.current_url
            
            # YANDEX ID из URL
            try:
                url_parts = data['url'].split('/')
                for part in url_parts:
                    if part.isdigit() and len(part) > 10:
                        data['yandex_id'] = part
                        break
            except:
                pass
            
            print(f"✅ Извлечены данные для: {data['name']}")
            return data
            
        except Exception as e:
            print(f"❌ Ошибка извлечения данных: {e}")
            return data
    
    def safe_get_text(self, element):
        """Безопасное получение текста из элемента"""
        try:
            return element.text.strip() if element else ""
        except:
            return ""
    
    def return_to_list(self):
        """Возврат к списку результатов"""
        try:
            # Нажатие ESC
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
        print("🚀 Запуск полного парсинга Яндекс Карт")
        print("=" * 60)
        
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
        print(f"📊 Начинаем обработку {len(results)} предприятий")
        print("-" * 60)
        
        # Обработка каждого результата
        for i, result in enumerate(results):
            print(f"\n📍 Предприятие {i+1}/{len(results)}")
            
            if self.click_business(result, i):
                business_data = self.extract_full_business_data()
                
                if business_data['name']:
                    self.businesses.append(business_data)
                    print(f"✅ Успешно: {business_data['name']}")
                    print(f"   📞 Телефонов: {len(business_data['phones'])}")
                    print(f"   🏷️ Категорий: {len(business_data['categories'])}")
                    print(f"   🛍️ Товаров: {len(business_data['products'])}")
                    print(f"   💰 Цен: {len(business_data['prices'])}")
                    print(f"   📱 Соцсетей: {sum(1 for v in business_data['social_links'].values() if v)}")
                else:
                    print("⚠️ Название не найдено")
                
                self.return_to_list()
            else:
                print("❌ Не удалось открыть карточку")
            
            time.sleep(2)  # Пауза между обработкой
        
        print(f"\n📈 Парсинг завершен!")
        print(f"✅ Успешно обработано: {len(self.businesses)} из {len(results)}")
        return True
    
    def save_results(self):
        """Сохранение результатов в разных форматах"""
        if not self.businesses:
            print("❌ Нет данных для сохранения")
            return
        
        os.makedirs("output", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Подробные данные в JSON
        json_filename = f"output/full_data_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.businesses, f, ensure_ascii=False, indent=2)
        print(f"💾 Полные данные (JSON): {json_filename}")
        
        # 2. Основные данные в Excel
        excel_data = []
        for business in self.businesses:
            row = {
                'Название': business['name'],
                'Верифицирован': 'Да' if business['verified'] else 'Нет',
                'Категории': ', '.join(business['categories']),
                'Рейтинг': business['rating'],
                'Отзывы': business['reviews_count'],
                'Награды': ', '.join(business['awards']),
                'Адрес': business['address'],
                'Телефоны': ', '.join(business['phones']),
                'Сайт': business['website'],
                'WhatsApp': business['social_links']['whatsapp'],
                'VK': business['social_links']['vk'],
                'Instagram': business['social_links']['instagram'],
                'Статус работы': business['working_hours']['current_status'],
                'Расписание': ', '.join(business['working_hours']['schedule']),
                'Услуги': ', '.join(business['services']),
                'Особенности': ', '.join(business['features']),
                'Товары': ', '.join(business['products']),
                'Цены': ', '.join(business['prices']),
                'Панорама': 'Да' if business['has_panorama'] else 'Нет',
                'Фото': business['photos_count'],
                'Истории': ', '.join(business['stories']),
                'URL': business['url'],
                'Yandex ID': business['yandex_id']
            }
            excel_data.append(row)
        
        excel_filename = f"output/businesses_{timestamp}.xlsx"
        df = pd.DataFrame(excel_data)
        df.to_excel(excel_filename, index=False)
        print(f"📊 Основные данные (Excel): {excel_filename}")
        
        # 3. Статистика
        stats = {
            'total_businesses': len(self.businesses),
            'with_phones': len([b for b in self.businesses if b['phones']]),
            'with_websites': len([b for b in self.businesses if b['website']]),
            'with_social': len([b for b in self.businesses if any(b['social_links'].values())]),
            'verified': len([b for b in self.businesses if b['verified']]),
            'with_panorama': len([b for b in self.businesses if b['has_panorama']]),
            'with_products': len([b for b in self.businesses if b['products']]),
            'avg_rating': sum(float(b['rating']) for b in self.businesses if b['rating'] and b['rating'].replace('.', '').isdigit()) / len([b for b in self.businesses if b['rating'] and b['rating'].replace('.', '').isdigit()]) if [b for b in self.businesses if b['rating'] and b['rating'].replace('.', '').isdigit()] else 0
        }
        
        print(f"\n📈 СТАТИСТИКА:")
        print(f"   📊 Всего предприятий: {stats['total_businesses']}")
        print(f"   📞 С телефонами: {stats['with_phones']}")
        print(f"   🌐 С сайтами: {stats['with_websites']}")
        print(f"   📱 С соцсетями: {stats['with_social']}")
        print(f"   ✅ Верифицированных: {stats['verified']}")
        print(f"   🏙️ С панорамой: {stats['with_panorama']}")
        print(f"   🛍️ С товарами: {stats['with_products']}")
        print(f"   ⭐ Средний рейтинг: {stats['avg_rating']:.1f}")
    
    def close(self):
        """Закрытие браузера"""
        if self.driver:
            print("\n👀 Браузер оставлен открытым для анализа")
            print("Нажмите Enter для закрытия...")
            input()
            
            self.driver.quit()
            print("🔚 Браузер закрыт")

def main():
    """Основная функция"""
    parser = FullYandexMapsParser()
    
    try:
        # URL для парсинга
        url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/"
        
        # Парсинг (ограничиваем 3 результатами для теста)
        if parser.parse(url, max_results=3):
            parser.save_results()
        
    except KeyboardInterrupt:
        print("\n⏹️ Парсинг остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        parser.close()

if __name__ == "__main__":
    main()
