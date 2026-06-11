#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Парсер Яндекс.Карт с прокруткой до заданного количества предприятий
Основан на точной структуре карточки предприятия
"""

import time
import os
import json
import pandas as pd
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

class YandexMapsTargetedParser:
    """Парсер с фокусом на конкретную структуру карточек предприятий"""
    
    def __init__(self, target_count=20):
        self.driver = None
        self.wait = None
        self.businesses = []
        self.processed_urls = set()
        self.target_count = target_count
        self.search_url = None  # Для хранения URL поиска
        
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
            self.wait = WebDriverWait(self.driver, 15)
            print("✅ Браузер запущен")
            return True
        except Exception as e:
            print(f"❌ Ошибка запуска браузера: {e}")
            return False
    
    def navigate_to_search(self, url):
        """Переход на страницу поиска"""
        print(f"📖 Переход на: {url}")
        self.search_url = url  # Сохраняем URL для восстановления
        try:
            self.driver.get(url)
            time.sleep(5)
            
            # Проверка на капчу
            if "SmartCaptcha" in self.driver.page_source or "Нам очень жаль" in self.driver.page_source:
                print("🔒 Обнаружена капча. Ожидание решения...")
                input("Решите капчу и нажмите Enter...")
                time.sleep(3)
            
            print("✅ Страница загружена")
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки страницы: {e}")
            return False
    
    def get_snippet_elements(self):
        """Получение элементов поисковой выдачи"""
        # Из диагностики видно, что лучший селектор для предприятий:
        selectors = [
            "//div[contains(@class, 'search-business-snippet-view')]",  # 85 элементов - это реальные предприятия!
            "//a[contains(@href, '/org/')]",  # 15 элементов - прямые ссылки на организации
            "//div[contains(@class, 'search-snippet-view')]", 
            "//li[contains(@class, 'serp-item')]"
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"✅ Найдено {len(elements)} элементов с селектором: {selector}")
                    # Дополнительная проверка - у элементов должен быть текст
                    valid_elements = []
                    for elem in elements:
                        try:
                            if elem.is_displayed() and elem.text.strip():
                                valid_elements.append(elem)
                        except:
                            continue
                    
                    if valid_elements:
                        print(f"✅ Из них {len(valid_elements)} валидных элементов")
                        return valid_elements
            except:
                continue
        
        print("⚠️ Элементы поисновой выдачи не найдены")
        return []
    
    def scroll_and_load_more(self):
        """Прокрутка страницы для загрузки новых результатов"""
        print("📜 Прокрутка для загрузки новых результатов...")
        
        # Найти контейнер с результатами
        container_selectors = [
            "//div[contains(@class, 'search-list-view')]",
            "//div[contains(@class, 'serp-list')]",
            "//div[contains(@class, 'search-results-view')]"
        ]
        
        container = None
        for selector in container_selectors:
            try:
                container = self.driver.find_element(By.XPATH, selector)
                if container.is_displayed():
                    break
            except:
                continue
        
        if container:
            # Прокрутка контейнера
            self.driver.execute_script("""
                arguments[0].scrollTo(0, arguments[0].scrollHeight);
            """, container)
        else:
            # Прокрутка всей страницы
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        time.sleep(3)  # Ждем загрузки новых элементов
    
    def collect_target_count(self):
        """Сбор результатов до достижения целевого количества"""
        print(f"🎯 Цель: собрать {self.target_count} предприятий")
        print("=" * 50)
        
        max_scroll_attempts = 15
        scroll_attempts = 0
        last_count = 0
        no_change_count = 0
        
        while scroll_attempts < max_scroll_attempts:
            # Получаем текущие элементы
            current_elements = self.get_snippet_elements()
            current_count = len(current_elements)
            
            print(f"📊 Попытка {scroll_attempts + 1}: найдено {current_count} результатов")
            
            # Если достигли цели
            if current_count >= self.target_count:
                print(f"✅ Цель достигнута! Найдено {current_count} результатов")
                return current_elements[:self.target_count]
            
            # Если количество не изменилось
            if current_count == last_count:
                no_change_count += 1
                print(f"⚠️ Количество не изменилось ({no_change_count}/3)")
                
                if no_change_count >= 3:
                    print("⏹️ Больше результатов не загружается")
                    break
            else:
                no_change_count = 0
                last_count = current_count
            
            # Прокрутка для загрузки новых результатов
            self.scroll_and_load_more()
            scroll_attempts += 1
        
        # Возвращаем то, что удалось собрать
        final_elements = self.get_snippet_elements()
        print(f"📈 Итого собрано: {len(final_elements)} результатов")
        return final_elements[:self.target_count]
    
    def click_on_snippet(self, snippet_element, index):
        """Клик по элементу поисковой выдачи"""
        print(f"🎯 Клик по предприятию {index + 1}")
        
        try:
            # Прокрутка к элементу
            self.driver.execute_script("arguments[0].scrollIntoView(true);", snippet_element)
            time.sleep(1)
            
            # Поиск кликабельного элемента (из диагностики знаем, что работает)
            clickable_selectors = [
                ".//div[contains(@class, 'search-business-snippet-view__title')]",  # Этот работает!
                ".//span[contains(@class, 'search-business-snippet-view__title')]",
                ".//a[contains(@class, 'search-snippet-view__title')]",
                ".//a[contains(@href, '/org/')]"  # Прямые ссылки на организации
            ]
            
            clicked = False
            for selector in clickable_selectors:
                try:
                    clickable = snippet_element.find_element(By.XPATH, selector)
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
                    self.driver.execute_script("arguments[0].click();", snippet_element)
                    clicked = True
                    print("🖱️ Клик по элементу выполнен")
                except:
                    print("❌ Клик не удался")
                    return False
            
            # Ожидание загрузки карточки
            time.sleep(4)
            
            # Проверка появления карточки
            try:
                card_element = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'business-card-view')]"))
                )
                if card_element.is_displayed():
                    print("✅ Карточка предприятия загружена")
                    return True
            except:
                pass
            
            print("⚠️ Карточка не загрузилась")
            return False
            
        except Exception as e:
            print(f"❌ Ошибка клика: {e}")
            return False
    
    def extract_business_data(self):
        """Извлечение данных из карточки предприятия на основе предоставленной структуры"""
        print("📊 Извлечение данных из карточки...")
        
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
                'youtube': '',
                'whatsapp': '',
                'vk': '',
                'ok': '',
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
            'accessibility': {},
            'has_panorama': False,
            'photos_count': 0,
            'stories': [],
            'coordinates': {'lat': '', 'lon': ''},
            'yandex_id': '',
            'url': '',
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            # URL и ID
            data['url'] = self.driver.current_url
            
            # Проверка на дубли
            if data['url'] in self.processed_urls:
                print("⚠️ Предприятие уже было обработано")
                return None
            
            self.processed_urls.add(data['url'])
            
            # НАЗВАНИЕ предприятия
            try:
                name_element = self.driver.find_element(By.XPATH, "//h1[contains(@class, 'card-title-view__title')]//a[contains(@class, 'card-title-view__title-link')]")
                data['name'] = self.safe_get_text(name_element)
            except:
                try:
                    name_element = self.driver.find_element(By.XPATH, "//h1[contains(@class, 'card-title-view__title')]")
                    data['name'] = self.safe_get_text(name_element)
                except:
                    pass
            
            # ВЕРИФИКАЦИЯ
            try:
                self.driver.find_element(By.XPATH, "//span[contains(@class, 'business-verified-badge')]")
                data['verified'] = True
            except:
                data['verified'] = False
            
            # КАТЕГОРИИ
            try:
                category_elements = self.driver.find_elements(By.XPATH, "//a[contains(@class, 'business-categories-view__category')]")
                data['categories'] = [self.safe_get_text(elem) for elem in category_elements if self.safe_get_text(elem)]
            except:
                pass
            
            # РЕЙТИНГ
            try:
                rating_element = self.driver.find_element(By.XPATH, "//span[contains(@class, 'business-rating-badge-view__rating-text')]")
                data['rating'] = self.safe_get_text(rating_element)
            except:
                pass
            
            # КОЛИЧЕСТВО ОТЗЫВОВ
            try:
                reviews_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'business-header-rating-view__text')]")
                reviews_text = self.safe_get_text(reviews_element)
                # Извлекаем числа из скобок
                numbers = re.findall(r'\((\d+)\)', reviews_text)
                if numbers:
                    data['reviews_count'] = numbers[0]
            except:
                pass
            
            # НАГРАДЫ
            try:
                award_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'business-header-awards-view__award-text')]")
                data['awards'] = [self.safe_get_text(elem) for elem in award_elements if self.safe_get_text(elem)]
            except:
                pass
            
            # АДРЕС
            try:
                address_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'business-contacts-view__address-link')]")
                data['address'] = self.safe_get_text(address_element)
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
                website_element = self.driver.find_element(By.XPATH, "//a[@itemprop='url']")
                data['website'] = website_element.get_attribute('href')
            except:
                pass
            
            # СОЦИАЛЬНЫЕ СЕТИ
            try:
                social_elements = self.driver.find_elements(By.XPATH, "//a[@itemprop='sameAs']")
                for social_elem in social_elements:
                    href = social_elem.get_attribute('href')
                    if 'youtube' in href:
                        data['social_links']['youtube'] = href
                    elif 'whatsapp' in href or 'wa.me' in href:
                        data['social_links']['whatsapp'] = href
                    elif 'vk.com' in href:
                        data['social_links']['vk'] = href
                    elif 'ok.ru' in href:
                        data['social_links']['ok'] = href
                    else:
                        data['social_links']['other'].append(href)
            except:
                pass
            
            # ВРЕМЯ РАБОТЫ
            try:
                status_element = self.driver.find_element(By.XPATH, "//div[contains(@class, 'business-card-working-status-view__text')]")
                data['working_hours']['current_status'] = self.safe_get_text(status_element)
                
                # График работы из мета-тегов
                schedule_metas = self.driver.find_elements(By.XPATH, "//meta[@itemprop='openingHours']")
                data['working_hours']['schedule'] = [meta.get_attribute('content') for meta in schedule_metas]
            except:
                pass
            
            # УСЛУГИ
            try:
                services_element = self.driver.find_element(By.XPATH, "//span[contains(@class, 'business-features-view__valued-value')]")
                services_text = self.safe_get_text(services_element)
                if services_text:
                    data['services'] = [s.strip() for s in services_text.split(',')]
            except:
                pass
            
            # ТОВАРЫ И ЦЕНЫ
            try:
                product_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'related-item-photo-view__title')]")
                data['products'] = [self.safe_get_text(elem) for elem in product_elements if self.safe_get_text(elem)]
                
                price_elements = self.driver.find_elements(By.XPATH, "//span[contains(@class, 'related-product-view__price')]")
                data['prices'] = [self.safe_get_text(elem) for elem in price_elements if self.safe_get_text(elem)]
            except:
                pass
            
            # ОСОБЕННОСТИ И ДОСТУПНОСТЬ
            try:
                feature_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'business-features-view__bool-text')]")
                data['features'] = [self.safe_get_text(elem) for elem in feature_elements if self.safe_get_text(elem)]
                
                # Доступность
                accessibility_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'business-features-view__valued')]")
                for elem in accessibility_elements:
                    text = self.safe_get_text(elem)
                    if 'доступность' in text.lower() or 'инвалид' in text.lower():
                        parts = text.split(':')
                        if len(parts) == 2:
                            data['accessibility'][parts[0].strip()] = parts[1].strip()
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
                data['stories'] = [self.safe_get_text(elem) for elem in story_elements if self.safe_get_text(elem)]
            except:
                pass
            
            # YANDEX ID из URL
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
        """Возврат к списку результатов"""
        print("🔙 Возврат к списку...")
        
        # Метод 1: ESC
        try:
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(2)
            
            # Проверяем, вернулись ли к списку
            if self.get_snippet_elements():
                print("✅ Возврат через ESC успешен")
                return True
        except:
            pass
        
        # Метод 2: Кнопка закрытия
        try:
            close_button = self.driver.find_element(By.XPATH, "//div[contains(@class, 'sidebar-view__close-button')]")
            close_button.click()
            time.sleep(2)
            
            if self.get_snippet_elements():
                print("✅ Возврат через кнопку закрытия успешен")
                return True
        except:
            pass
        
        # Метод 3: Кнопка "Назад" браузера
        try:
            self.driver.back()
            time.sleep(3)
            
            if self.get_snippet_elements():
                print("✅ Возврат через кнопку назад успешен")
                return True
        except:
            pass
        
        # Метод 4: Перезагрузка страницы поиска
        try:
            current_url = self.driver.current_url
            # Ищем URL поиска в истории или строим заново
            if '/search/' in current_url:
                search_url = current_url.split('/org/')[0]  # Убираем часть с организацией
                self.driver.get(search_url)
                time.sleep(4)
                
                if self.get_snippet_elements():
                    print("✅ Возврат через перезагрузку поиска успешен")
                    return True
        except:
            pass
        
        print("⚠️ Не удалось вернуться к списку")
        return False
    
    def parse(self, url):
        """Основной метод парсинга"""
        print("🚀 Запуск целевого парсинга Яндекс.Карт")
        print("=" * 60)
        print(f"🎯 ЦЕЛЬ: {self.target_count} предприятий")
        print("=" * 60)
        
        if not self.setup_driver():
            return False
        
        if not self.navigate_to_search(url):
            return False
        
        # Сбор элементов до нужного количества
        initial_elements = self.collect_target_count()
        if not initial_elements:
            print("❌ Результаты поиска не найдены")
            return False
        
        target_count = min(len(initial_elements), self.target_count)
        print(f"\n📊 НАЧИНАЕМ ОБРАБОТКУ {target_count} ПРЕДПРИЯТИЙ")
        print("=" * 60)
        
        # Обработка каждого результата по индексу
        processed_count = 0
        current_index = 0
        
        while processed_count < target_count and current_index < target_count * 2:  # Защита от бесконечного цикла
            print(f"\n📍 Попытка {current_index + 1} (обработано: {processed_count}/{target_count})")
            
            # Пересобираем элементы после каждого возврата
            current_elements = self.get_snippet_elements()
            
            if not current_elements or current_index >= len(current_elements):
                print(f"⚠️ Недостаточно элементов. Найдено: {len(current_elements)}, нужен индекс: {current_index}")
                break
            
            snippet = current_elements[current_index]
            
            if self.click_on_snippet(snippet, current_index):
                business_data = self.extract_business_data()
                
                if business_data and business_data['name']:
                    self.businesses.append(business_data)
                    processed_count += 1
                    print(f"✅ Успешно обработано {processed_count}/{target_count}: {business_data['name']}")
                    print(f"   📞 Телефонов: {len(business_data['phones'])}")
                    print(f"   🏷️ Категорий: {len(business_data['categories'])}")
                    print(f"   🛍️ Товаров: {len(business_data['products'])}")
                    print(f"   ⭐ Рейтинг: {business_data['rating']}")
                else:
                    print("⚠️ Данные не извлечены или дубликат")
                
                # Возвращаемся к списку
                if not self.return_to_list():
                    print("❌ Не удалось вернуться к списку, попробуем продолжить")
                    # Попытка восстановления - перезагрузка поиска
                    if self.search_url:
                        self.navigate_to_search(self.search_url)
                        time.sleep(3)
                
                time.sleep(3)  # Увеличенная пауза для стабилизации
            else:
                print("❌ Не удалось открыть карточку")
            
            current_index += 1
            time.sleep(2)  # Пауза между предприятиями
        
        print(f"\n📈 ПАРСИНГ ЗАВЕРШЕН!")
        print(f"✅ Успешно обработано: {len(self.businesses)} из {target_count}")
        print(f"🎯 Цель ({self.target_count}): {'ДОСТИГНУТА' if len(self.businesses) >= self.target_count else 'НЕ ДОСТИГНУТА'}")
        return True
    
    def save_results(self):
        """Сохранение результатов"""
        if not self.businesses:
            print("❌ Нет данных для сохранения")
            return
        
        os.makedirs("output", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON с полными данными
        json_filename = f"output/targeted_data_{timestamp}.json"
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
                'Награды': ', '.join(business['awards']),
                'Адрес': business['address'],
                'Телефоны': ', '.join(business['phones']),
                'Сайт': business['website'],
                'WhatsApp': business['social_links']['whatsapp'],
                'VK': business['social_links']['vk'],
                'YouTube': business['social_links']['youtube'],
                'Статус работы': business['working_hours']['current_status'],
                'Услуги': ', '.join(business['services'][:5]),  # Первые 5 услуг
                'Товары': len(business['products']),
                'Панорама': 'Да' if business['has_panorama'] else 'Нет',
                'Истории': len(business['stories']),
                'URL': business['url'],
                'Yandex ID': business['yandex_id']
            }
            excel_data.append(row)
        
        excel_filename = f"output/targeted_businesses_{timestamp}.xlsx"
        df = pd.DataFrame(excel_data)
        df.to_excel(excel_filename, index=False)
        print(f"📊 Основные данные: {excel_filename}")
        
        # Статистика
        print(f"\n📈 СТАТИСТИКА:")
        print(f"   📊 Всего предприятий: {len(self.businesses)}")
        print(f"   📞 С телефонами: {len([b for b in self.businesses if b['phones']])}")
        print(f"   🌐 С сайтами: {len([b for b in self.businesses if b['website']])}")
        print(f"   ✅ Верифицированных: {len([b for b in self.businesses if b['verified']])}")
        print(f"   🏆 С наградами: {len([b for b in self.businesses if b['awards']])}")
        print(f"   📺 С панорамой: {len([b for b in self.businesses if b['has_panorama']])}")
    
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
    # URL из предоставленного примера
    url = "https://yandex.ru/maps/39/rostov-na-donu/search/Ростов%20на%20дону%20суворовский%20стоматология/?ll=39.806284%2C47.275656&sctx=ZAAAAAgCEAAaKAoSCbnEkQci10NAESl4CrlSn0dAEhIJ98ySADW1zj8R1lJA2v8Aqz8iBgABAgMEBSgKOABA0YgGSAFqAnJ1nQHNzMw9oAEAqAEAvQHFGEBwwgElzKy6tfoGxpeW5AXL5fTcA9Ka8PoDwpzMogT4sL%2FgA%2Fyw57rlBoICStCg0L7RgdGC0L7QsiDQvdCwINC00L7QvdGDINGB0YPQstC%2B0YDQvtCy0YHQutC40Lkg0YHRgtC%2B0LzQsNGC0L7Qu9C%2B0LPQuNGPigIAkgICMzmaAgxkZXNrdG9wLW1hcHPaAigKEgnfWbvtQuFDQBGw%2Fs8gd6FHQBISCYBnXaPlQN0%2FEQA8uDtrt7k%2F4AIB&sll=39.806284%2C47.275656&sspn=0.914172%2C0.200856&z=10.61"
    
    target_count = 15  # Целевое количество предприятий
    
    parser = YandexMapsTargetedParser(target_count=target_count)
    
    try:
        if parser.parse(url):
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
