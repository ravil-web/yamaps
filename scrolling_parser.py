#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Парсер с прокруткой блока результатов до заданного количества предприятий
Прокручивает список результатов пока не найдет нужное количество предприятий
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
from selenium.webdriver.common.action_chains import ActionChains

class ScrollingYandexMapsParser:
    """Парсер с прокруткой блока результатов до нужного количества"""
    
    def __init__(self):
        self.driver = None
        self.businesses = []
        self.wait = None
        self.processed_urls = set()  # Для избежания дублей
    
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
            print("✅ Страница загружена")
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки страницы: {e}")
            return False
    
    def scroll_results_container(self):
        """Прокрутка контейнера с результатами для загрузки новых"""
        print("📜 Прокрутка контейнера результатов...")
        
        try:
            # Поиск контейнера с результатами
            container_selectors = [
                "//div[contains(@class, 'search-list-view')]",
                "//div[contains(@class, 'search-results')]", 
                "//div[contains(@class, 'serp-list')]",
                "//div[contains(@class, 'companies-list')]"
            ]
            
            container = None
            for selector in container_selectors:
                try:
                    container = self.driver.find_element(By.XPATH, selector)
                    if container.is_displayed():
                        print(f"✅ Найден контейнер: {selector}")
                        break
                except:
                    continue
            
            if not container:
                print("⚠️ Контейнер не найден, прокручиваем всю страницу")
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                return
            
            # Прокрутка контейнера
            for i in range(5):  # Максимум 5 прокруток за раз
                # Прокрутка контейнера до конца
                self.driver.execute_script("""
                    arguments[0].scrollTo(0, arguments[0].scrollHeight);
                """, container)
                
                time.sleep(2)  # Ждем загрузки новых элементов
                
                # Проверяем появились ли новые элементы
                current_results = self.get_current_results_count()
                print(f"   📊 Прокрутка {i+1}: видно {current_results} результатов")
                
                # Небольшая пауза между прокрутками
                time.sleep(1)
                
        except Exception as e:
            print(f"❌ Ошибка прокрутки: {e}")
            # Фоллбек - прокрутка всей страницы
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
    
    def get_current_results_count(self):
        """Получение текущего количества видимых результатов"""
        selectors = [
            "//div[contains(@class, 'search-snippet-view')]",
            "//li[contains(@class, 'serp-item')]", 
            "//div[contains(@class, 'business-snippet-view')]",
            "//div[contains(@class, 'search-business-snippet-view')]"
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    return len(elements)
            except:
                continue
        return 0
    
    def collect_results_with_scrolling(self, target_count):
        """Сбор результатов с прокруткой до нужного количества"""
        print(f"🎯 Цель: собрать {target_count} предприятий")
        print("=" * 50)
        
        max_scroll_attempts = 20  # Максимум попыток прокрутки
        scroll_attempts = 0
        last_count = 0
        no_change_attempts = 0
        
        while scroll_attempts < max_scroll_attempts:
            # Получаем текущее количество результатов
            current_count = self.get_current_results_count()
            print(f"📊 Попытка {scroll_attempts + 1}: найдено {current_count} результатов")
            
            # Если достигли цели
            if current_count >= target_count:
                print(f"✅ Цель достигнута! Найдено {current_count} результатов")
                break
            
            # Если количество не изменилось
            if current_count == last_count:
                no_change_attempts += 1
                print(f"⚠️ Количество не изменилось ({no_change_attempts}/3)")
                
                if no_change_attempts >= 3:
                    print("⏹️ Больше результатов не загружается")
                    break
            else:
                no_change_attempts = 0
                last_count = current_count
            
            # Прокручиваем для загрузки новых результатов
            self.scroll_results_container()
            scroll_attempts += 1
            
            # Дополнительная пауза между циклами
            time.sleep(2)
        
        # Финальный подсчет
        final_count = self.get_current_results_count()
        print(f"📈 Итого найдено: {final_count} результатов после {scroll_attempts} прокруток")
        
        return self.get_search_results()
    
    def get_search_results(self):
        """Получение всех видимых результатов поиска"""
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
                    print(f"✅ Получено {len(elements)} результатов с селектором: {selector}")
                    break
            except:
                continue
        
        return results
    
    def click_business(self, result_element, index):
        """Клик по предприятию и переход к карточке"""
        print(f"🎯 Клик по предприятию {index + 1}")
        
        try:
            # Прокрутка к элементу
            self.driver.execute_script("arguments[0].scrollIntoView(true);", result_element)
            time.sleep(1)
            
            # Различные способы клика
            clickable_selectors = [
                ".//span[contains(@class, 'search-business-snippet-view__title')]",
                ".//a[contains(@class, 'search-snippet-view__title')]",
                ".//div[contains(@class, 'search-snippet-view__title')]",
                ".//span[contains(@class, 'business-snippet-view__name')]"
            ]
            
            clicked = False
            for selector in clickable_selectors:
                try:
                    clickable = result_element.find_element(By.XPATH, selector)
                    if clickable.is_displayed():
                        # Пробуем разные способы клика
                        try:
                            clickable.click()
                        except:
                            try:
                                ActionChains(self.driver).move_to_element(clickable).click().perform()
                            except:
                                self.driver.execute_script("arguments[0].click();", clickable)
                        
                        clicked = True
                        print("🖱️ Клик выполнен")
                        break
                except:
                    continue
            
            if not clicked:
                # Клик по самому элементу
                try:
                    self.driver.execute_script("arguments[0].click();", result_element)
                    clicked = True
                    print("🖱️ Клик по элементу выполнен")
                except:
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
        """Извлечение всех данных из карточки предприятия"""
        print("📊 Извлечение данных...")
        
        data = {
            'name': '',
            'verified': False,
            'categories': [],
            'rating': '',
            'reviews_count': '',
            'awards': [],
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
            'working_hours': {
                'current_status': '',
                'schedule': []
            },
            'services': [],
            'products': [],
            'prices': [],
            'features': [],
            'has_panorama': False,
            'photos_count': 0,
            'stories': [],
            'description': '',
            'coordinates': {'lat': '', 'lon': ''},
            'yandex_id': '',
            'url': '',
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            # URL и ID
            data['url'] = self.driver.current_url
            
            # Проверяем на дубли
            if data['url'] in self.processed_urls:
                print("⚠️ Предприятие уже было обработано")
                return None
            
            self.processed_urls.add(data['url'])
            
            # НАЗВАНИЕ
            try:
                title_elem = self.driver.find_element(By.XPATH, "//h1[contains(@class, 'card-title-view__title')]")
                data['name'] = self.safe_get_text(title_elem)
                
                # Верификация
                try:
                    self.driver.find_element(By.XPATH, "//span[contains(@class, 'business-verified-badge')]")
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
            
            # РЕЙТИНГ
            try:
                rating_elem = self.driver.find_element(By.XPATH, "//span[contains(@class, 'business-rating-badge-view__rating-text')]")
                data['rating'] = self.safe_get_text(rating_elem)
            except:
                pass
            
            # ОТЗЫВЫ
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
                try:
                    address_meta = self.driver.find_element(By.XPATH, "//meta[@itemprop='address']")
                    data['address'] = address_meta.get_attribute('content')
                except:
                    pass
            
            # ТЕЛЕФОНЫ
            try:
                phone_elements = self.driver.find_elements(By.XPATH, "//span[@itemprop='telephone']")
                data['phones'] = [self.safe_get_text(elem) for elem in phone_elements if self.safe_get_text(elem)]
            except:
                pass
            
            # ВЕБ-САЙТ
            try:
                website_elem = self.driver.find_element(By.XPATH, "//a[@itemprop='url']")
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
                
                schedule_metas = self.driver.find_elements(By.XPATH, "//meta[@itemprop='openingHours']")
                data['working_hours']['schedule'] = [meta.get_attribute('content') for meta in schedule_metas]
            except:
                pass
            
            # УСЛУГИ
            try:
                services_elem = self.driver.find_element(By.XPATH, "//span[contains(@class, 'business-features-view__valued-value')]")
                services_text = self.safe_get_text(services_elem)
                if services_text:
                    data['services'] = [s.strip() for s in services_text.split(',')]
            except:
                pass
            
            # ОСОБЕННОСТИ
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
                self.driver.find_element(By.XPATH, "//button[contains(@class, 'card-media-preview _type_panorama')]")
                data['has_panorama'] = True
            except:
                data['has_panorama'] = False
            
            # ИСТОРИИ
            try:
                story_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'story-preview__title')]")
                data['stories'] = [self.safe_get_text(elem) for elem in story_elements]
            except:
                pass
            
            # YANDEX ID
            try:
                url_parts = data['url'].split('/')
                for part in url_parts:
                    if part.isdigit() and len(part) > 10:
                        data['yandex_id'] = part
                        break
            except:
                pass
            
            print(f"✅ Данные извлечены: {data['name']}")
            return data
            
        except Exception as e:
            print(f"❌ Ошибка извлечения: {e}")
            return data
    
    def safe_get_text(self, element):
        """Безопасное получение текста"""
        try:
            return element.text.strip() if element else ""
        except:
            return ""
    
    def return_to_list(self):
        """Возврат к списку"""
        try:
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(2)
        except:
            try:
                self.driver.back()
                time.sleep(3)
            except:
                pass
    
    def parse(self, url, target_count=20):
        """Основной метод парсинга с прокруткой до нужного количества"""
        print("🚀 Запуск парсинга с прокруткой блока результатов")
        print("=" * 60)
        print(f"🎯 ЦЕЛЬ: {target_count} предприятий")
        print("=" * 60)
        
        if not self.setup_driver():
            return False
        
        if not self.navigate_to_search(url):
            return False
        
        # Сбор результатов с прокруткой
        results = self.collect_results_with_scrolling(target_count)
        if not results:
            print("❌ Результаты поиска не найдены")
            return False
        
        # Ограничиваем до нужного количества
        results = results[:target_count]
        print(f"\n📊 НАЧИНАЕМ ОБРАБОТКУ {len(results)} ПРЕДПРИЯТИЙ")
        print("=" * 60)
        
        # Обработка каждого результата
        for i, result in enumerate(results):
            print(f"\n📍 Предприятие {i+1}/{len(results)} (всего обработано: {len(self.businesses)})")
            
            if self.click_business(result, i):
                business_data = self.extract_full_business_data()
                
                if business_data and business_data['name']:
                    self.businesses.append(business_data)
                    print(f"✅ Успешно: {business_data['name']}")
                    print(f"   📞 Телефонов: {len(business_data['phones'])}")
                    print(f"   🏷️ Категорий: {len(business_data['categories'])}")
                    print(f"   🛍️ Товаров: {len(business_data['products'])}")
                else:
                    print("⚠️ Данные не извлечены или дубликат")
                
                self.return_to_list()
                time.sleep(1)  # Пауза перед возвратом к списку
            else:
                print("❌ Не удалось открыть карточку")
            
            time.sleep(2)  # Пауза между предприятиями
        
        print(f"\n📈 ПАРСИНГ ЗАВЕРШЕН!")
        print(f"✅ Успешно обработано: {len(self.businesses)} из {len(results)}")
        print(f"🎯 Цель ({target_count}): {'ДОСТИГНУТА' if len(self.businesses) >= target_count else 'НЕ ДОСТИГНУТА'}")
        return True
    
    def save_results(self):
        """Сохранение результатов"""
        if not self.businesses:
            print("❌ Нет данных для сохранения")
            return
        
        os.makedirs("output", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON с полными данными
        json_filename = f"output/scrolling_data_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(self.businesses, f, ensure_ascii=False, indent=2)
        print(f"💾 Полные данные: {json_filename}")
        
        # Excel с основными данными
        excel_data = []
        for business in self.businesses:
            row = {
                'Название': business['name'],
                'Верифицирован': 'Да' if business['verified'] else 'Нет',
                'Категории': ', '.join(business['categories']),
                'Рейтинг': business['rating'],
                'Отзывы': business['reviews_count'],
                'Адрес': business['address'],
                'Телефоны': ', '.join(business['phones']),
                'Сайт': business['website'],
                'WhatsApp': business['social_links']['whatsapp'],
                'VK': business['social_links']['vk'],
                'Услуги': ', '.join(business['services']),
                'Товары': len(business['products']),
                'URL': business['url'],
                'Yandex ID': business['yandex_id']
            }
            excel_data.append(row)
        
        excel_filename = f"output/scrolling_businesses_{timestamp}.xlsx"
        df = pd.DataFrame(excel_data)
        df.to_excel(excel_filename, index=False)
        print(f"📊 Основные данные: {excel_filename}")
        
        # Статистика
        print(f"\n📈 СТАТИСТИКА:")
        print(f"   📊 Всего предприятий: {len(self.businesses)}")
        print(f"   📞 С телефонами: {len([b for b in self.businesses if b['phones']])}")
        print(f"   🌐 С сайтами: {len([b for b in self.businesses if b['website']])}")
        print(f"   ✅ Верифицированных: {len([b for b in self.businesses if b['verified']])}")
    
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
    parser = ScrollingYandexMapsParser()
    
    try:
        url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/"
        target_count = 15  # Целевое количество предприятий
        
        if parser.parse(url, target_count=target_count):
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
