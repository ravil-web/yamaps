#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Окончательно рабочий парсер Яндекс.Карт
Решает проблемы с кликами и навигацией
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
from config import TARGET_BUSINESSES_COUNT

class FinalWorkingParser:
    """Финальная рабочая версия парсера"""
    
    def __init__(self, target_count=None):
        self.driver = None
        self.wait = None
        self.businesses = []
        self.processed_urls = set()
        # Используем значение из конфигурации, если не указано явно
        self.target_count = target_count if target_count is not None else TARGET_BUSINESSES_COUNT
        self.search_url = None
    
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
        options.add_argument('--disable-logging')
        options.add_argument('--log-level=3')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-component-extensions-with-background-pages')
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-system-font-check')
        options.add_argument('--disable-component-update')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-features=TranslateUI')
        
        # Дополнительные настройки для подавления логов и улучшения производительности
        options.add_argument('--disable-logging')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor,TranslateUI,BlinkGenPropertyTrees')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-client-side-phishing-detection')
        options.add_argument('--disable-sync')
        options.add_argument('--disable-translate')
        options.add_argument('--hide-scrollbars')
        options.add_argument('--mute-audio')
        options.add_argument('--no-first-run')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-prompt-on-repost')
        options.add_argument('--disable-hang-monitor')
        options.add_argument('--disable-prompt-on-repost')
        options.add_argument('--disable-domain-reliability')
        options.add_argument('--disable-features=AudioServiceOutOfProcess')
        options.add_argument('--disable-features=MediaRouter')
        options.add_argument('--disable-features=WebRtcHideLocalIpsWithMdns')
        
        # Подавление всех логов
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--silent')
        options.add_argument('--disable-logging')
        options.add_argument('--log-level=3')
        options.add_argument('--disable-dev-shm-usage')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(5)
            self.wait = WebDriverWait(self.driver, 10)
            print("✅ Браузер запущен")
            return True
        except Exception as e:
            print(f"❌ Ошибка запуска браузера: {e}")
            return False
    
    def navigate_to_search(self, url):
        """Переход на страницу поиска"""
        print(f"📖 Переход на: {url}")
        
        # Проверяем, что URL валидный
        if not url or not url.startswith('http'):
            print(f"❌ Неверный URL: {url}")
            return False
            
        self.search_url = url
        try:
            self.driver.get(url)
            time.sleep(5)
            
            # Проверяем капчу
            if "SmartCaptcha" in self.driver.page_source:
                print("🔒 Обнаружена капча. Ожидание решения...")
                input("Решите капчу и нажмите Enter...")
                time.sleep(3)
            
            print("✅ Страница загружена")
            return True
        except Exception as e:
            print(f"❌ Ошибка загрузки страницы: {e}")
            return False
    
    def get_business_links(self):
        """Получение прямых ссылок на предприятия с оптимизированным поиском"""
        print("🔍 Поиск ссылок на предприятия...")
        
        # Прокручиваем блок с предприятиями
        self.scroll_to_load_more()
        
        # Ищем прямые ссылки на организации
        try:
            main_links = []
            seen_ids = set()
            
            # Основные селекторы для поиска ссылок на предприятия
            link_selectors = [
                "//a[contains(@href, '/org/') and not(contains(@href, '/gallery/')) and not(contains(@href, '/reviews/')) and not(contains(@href, '/features/'))]",
                "//a[contains(@href, '/org/') and not(contains(@href, '/gallery/')) and not(contains(@href, '/reviews/'))]",
                "//a[contains(@href, '/org/')]",
                "//a[contains(@class, 'search-result-snippet-view__link')]",
                "//a[contains(@class, 'search-result-snippet-view')]",
                "//a[contains(@class, 'business-snippet-view')]",
                "//a[contains(@class, 'orgpage-snippet-view')]",
                "//a[contains(@class, 'snippet-view')]",
                "//a[contains(@class, 'search-result')]",
                "//a[contains(@class, 'business')]",
                "//a[contains(@class, 'org')]"
            ]
            
            for selector in link_selectors:
                try:
                    self.driver.implicitly_wait(2)
                    org_links = self.driver.find_elements(By.XPATH, selector)
                    
                    if org_links:
                        print(f"   📊 Найдено {len(org_links)} ссылок с селектором: {selector[:50]}...")
                        
                        for link in org_links:
                            try:
                                href = link.get_attribute('href')
                                if href and '/org/' in href:
                                    # Извлекаем ID организации из URL
                                    parts = href.split('/org/')
                                    if len(parts) > 1:
                                        org_part = parts[1].split('/')[1] if len(parts[1].split('/')) > 1 else parts[1]
                                        if org_part and org_part.isdigit() and org_part not in seen_ids:
                                            seen_ids.add(org_part)
                                            main_links.append(href)
                            except:
                                continue
                        
                        if main_links:
                            break
                            
                except:
                    continue
                finally:
                    self.driver.implicitly_wait(10)
            
            # Дополнительный поиск по тексту ссылок
            if not main_links:
                print("   🔍 Дополнительный поиск по тексту ссылок...")
                try:
                    text_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/org/')]")
                    for link in text_links:
                        try:
                            href = link.get_attribute('href')
                            text = link.text.strip()
                            if href and '/org/' in href and text and len(text) > 3:
                                parts = href.split('/org/')
                                if len(parts) > 1:
                                    org_part = parts[1].split('/')[1] if len(parts[1].split('/')) > 1 else parts[1]
                                    if org_part and org_part.isdigit() and org_part not in seen_ids:
                                        seen_ids.add(org_part)
                                        main_links.append(href)
                        except:
                            continue
                except:
                    pass
            
            # Если все еще ничего не найдено, пробуем альтернативные селекторы
            if not main_links:
                print("   🔍 Альтернативный поиск предприятий...")
                try:
                    # Ищем по классам контейнеров предприятий
                    container_selectors = [
                        "//div[contains(@class, 'search-result-snippet-view')]//a",
                        "//div[contains(@class, 'business-snippet-view')]//a",
                        "//div[contains(@class, 'orgpage-snippet-view')]//a",
                        "//div[contains(@class, 'snippet-view')]//a",
                        "//div[contains(@class, 'search-result')]//a",
                        "//div[contains(@class, 'business')]//a",
                        "//div[contains(@class, 'org')]//a",
                        "//div[contains(@class, 'result')]//a"
                    ]
                    
                    for selector in container_selectors:
                        try:
                            self.driver.implicitly_wait(2)
                            container_links = self.driver.find_elements(By.XPATH, selector)
                            
                            if container_links:
                                print(f"   📊 Найдено {len(container_links)} ссылок в контейнерах с селектором: {selector[:50]}...")
                                
                                for link in container_links:
                                    try:
                                        href = link.get_attribute('href')
                                        if href and '/org/' in href:
                                            parts = href.split('/org/')
                                            if len(parts) > 1:
                                                org_part = parts[1].split('/')[1] if len(parts[1].split('/')) > 1 else parts[1]
                                                if org_part and org_part.isdigit() and org_part not in seen_ids:
                                                    seen_ids.add(org_part)
                                                    main_links.append(href)
                                    except:
                                        continue
                                
                                if main_links:
                                    break
                                    
                        except:
                            continue
                        finally:
                            self.driver.implicitly_wait(10)
                except:
                    pass
            
            # Дополнительный поиск, если ссылок мало
            if len(main_links) < 10:
                print(f"   ⚠️ Найдено мало ссылок ({len(main_links)}), дополнительный поиск...")
                
                # Простой поиск по всем ссылкам на странице
                try:
                    all_links = self.driver.find_elements(By.TAG_NAME, "a")
                    print(f"   📊 Проверяем {len(all_links)} ссылок на странице")
                    
                    for link in all_links:
                        try:
                            href = link.get_attribute('href')
                            if href and '/org/' in href and 'yandex.ru' in href:
                                parts = href.split('/org/')
                                if len(parts) > 1:
                                    org_part = parts[1].split('/')[1] if len(parts[1].split('/')) > 1 else parts[1]
                                    if org_part and org_part.isdigit() and org_part not in seen_ids:
                                        seen_ids.add(org_part)
                                        main_links.append(href)
                        except:
                            continue
                except Exception as e:
                    print(f"   ⚠️ Ошибка при дополнительном поиске: {e}")
            
            print(f"✅ Найдено {len(main_links)} уникальных ссылок на предприятия")
            return main_links
            
        except Exception as e:
            print(f"❌ Ошибка поиска ссылок: {e}")
            return []
    
    def scroll_to_load_more(self):
        """Прокрутка блока с предприятиями для загрузки больше контента"""
        print("📜 Прокрутка блока с предприятиями...")
        
        # Ждем загрузки страницы
        time.sleep(2)
        
        # Получаем начальное количество элементов
        initial_elements = self.count_business_elements()
        print(f"   📊 Начальное количество элементов: {initial_elements}")
        
        # Находим блок с результатами поиска
        results_container = self.find_results_container()
        
        if results_container:
            print(f"   ✅ Найден блок результатов, используем прокрутку контейнера")
            self.scroll_container_method(results_container, initial_elements)
        else:
            print("   ⚠️ Блок результатов не найден, используем прокрутку страницы")
            self.scroll_page_fallback()
    
    def scroll_container_method(self, container, initial_elements):
        """Прокрутка через контейнер"""
        print(f"   🔄 Начинаем прокрутку контейнера...")
        scroll_attempts = 0
        max_scrolls = 5  # Ограничиваем до 5 итераций, так как все находится на пятой
        no_change_count = 0
        max_no_change = 2  # Уменьшаем лимит для быстрого завершения
        
        while scroll_attempts < max_scrolls and no_change_count < max_no_change:
            print(f"   🔄 Итерация {scroll_attempts + 1}/{max_scrolls}")
            elements_before = self.count_business_elements()
            print(f"   📊 Элементов до прокрутки: {elements_before}")
            
            # Прокручиваем блок результатов
            print(f"   📜 Выполняем прокрутку...")
            self.scroll_results_container(container)
            
            # Ждем загрузки
            print(f"   ⏳ Ожидание загрузки...")
            time.sleep(1.0)  # Уменьшаем время ожидания для быстрой работы
            
            elements_after = self.count_business_elements()
            print(f"   📊 Элементов после прокрутки: {elements_after}")
            
            if elements_after > elements_before:
                print(f"   ✅ Загружено: +{elements_after - elements_before} (всего: {elements_after})")
                no_change_count = 0
            else:
                no_change_count += 1
                print(f"   ⏳ Прокрутка {scroll_attempts + 1}: без изменений ({no_change_count}/{max_no_change})")
            
            scroll_attempts += 1
            
            # Проверяем кнопки загрузки
            if no_change_count >= 2:
                print(f"   🔘 Поиск кнопок загрузки...")
                if self.click_load_more_buttons():
                    no_change_count = 0
                    time.sleep(1.0)  # Уменьшаем время ожидания после клика для быстрой работы
                    print(f"   ✅ Кнопка загрузки нажата")
                else:
                    print(f"   ❌ Кнопки загрузки не найдены")
        
        # Финальная попытка с более агрессивной прокруткой
        if no_change_count >= max_no_change:
            print("   🔄 Финальная агрессивная прокрутка...")
            self.aggressive_scroll()
        
        final_elements = self.count_business_elements()
        print(f"   📈 Финальное количество: {final_elements} (+{final_elements - initial_elements})")
    
    def aggressive_scroll(self):
        """Агрессивная прокрутка для загрузки максимального количества контента"""
        try:
            print("   🚀 Агрессивная прокрутка...")
            
            # Получаем начальное количество элементов
            initial_count = self.count_business_elements()
            print(f"   📊 Начальное количество: {initial_count}")
            
            # Множественные стратегии прокрутки
            for i in range(5):  # Ограничиваем до 5 циклов для оптимизации
                print(f"   🔄 Цикл {i+1}/5")
                
                # 1. Прокрутка вниз
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(0.2)  # Уменьшаем время ожидания для быстрой работы
                
                # 2. Прокрутка до конца
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.2)
                
                # 3. Проверяем кнопки загрузки
                if self.click_load_more_buttons():
                    time.sleep(1.0)  # Уменьшаем время ожидания для быстрой работы
                    print(f"   ✅ Кнопка загрузки нажата")
                
                # 4. Прокрутка еще немного
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(0.1)
                
                # 5. Проверяем, загрузился ли новый контент
                if i % 2 == 0:  # Каждые 2 цикла
                    current_count = self.count_business_elements()
                    print(f"   📊 Текущее количество элементов: {current_count}")
                    
                    # Если нет изменений в течение 2 циклов, прекращаем
                    if current_count == initial_count and i > 1:
                        print(f"   ✅ Достигнут максимум контента, прекращаем прокрутку")
                        break
                    
                    initial_count = current_count
            
            print("   ✅ Агрессивная прокрутка завершена")
            
        except Exception as e:
            print(f"   ⚠️ Ошибка агрессивной прокрутки: {e}")
    
    def find_results_container(self):
        """Поиск контейнера с результатами поиска"""
        try:
            # Специфичные селекторы для Яндекс.Карт
            container_selectors = [
                # Основные селекторы Яндекс.Карт
                "//div[contains(@class, 'search-list-view')]",
                "//div[contains(@class, 'search-list')]",
                "//div[contains(@class, 'search-results')]",
                "//div[contains(@class, 'results-list')]",
                "//div[contains(@class, 'business-list')]",
                "//div[contains(@class, 'org-list')]",
                "//div[contains(@class, 'list-view')]",
                "//div[contains(@class, 'search')]",
                "//div[contains(@class, 'results')]",
                "//div[contains(@class, 'list')]",
                "//div[contains(@class, 'business')]",
                "//div[contains(@class, 'org')]",
                # Дополнительные селекторы
                "//div[contains(@class, 'snippet')]",
                "//div[contains(@class, 'item')]",
                "//div[contains(@class, 'card')]",
                "//div[contains(@class, 'block')]"
            ]
            
            for selector in container_selectors:
                try:
                    containers = self.driver.find_elements(By.XPATH, selector)
                    for container in containers:
                        if container.is_displayed():
                            # Проверяем, что в контейнере есть ссылки на предприятия
                            org_links = container.find_elements(By.XPATH, ".//a[contains(@href, '/org/')]")
                            if len(org_links) > 0:
                                print(f"   🎯 Найден контейнер с {len(org_links)} ссылками (селектор: {selector})")
                                return container
                except:
                    continue
            
            # Если не нашли контейнер, пробуем найти по родительскому элементу
            print("   🔍 Поиск по родительским элементам...")
            try:
                # Ищем все ссылки на предприятия и их родительские контейнеры
                org_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/org/')]")
                if org_links:
                    # Берем первый элемент и ищем его родительский контейнер
                    first_link = org_links[0]
                    parent = first_link.find_element(By.XPATH, "./ancestor::div[contains(@class, 'search') or contains(@class, 'list') or contains(@class, 'result') or contains(@class, 'business') or contains(@class, 'org')][1]")
                    if parent and parent.is_displayed():
                        print(f"   🎯 Найден родительский контейнер")
                        return parent
            except:
                pass
            
            return None
        except Exception as e:
            print(f"   ⚠️ Ошибка поиска контейнера: {e}")
            return None
    
    def scroll_results_container(self, container):
        """Прокрутка страницы для загрузки контента в контейнер"""
        try:
            print(f"   📜 Начинаем прокрутку страницы...")
            
            # Множественные стратегии прокрутки для максимальной эффективности
            
            # 1. Прокрутка вниз пошагово
            print(f"   📜 Шаг 1: Прокрутка вниз пошагово...")
            for i in range(3):
                self.driver.execute_script("window.scrollBy(0, 600);")
                time.sleep(0.3)
            
            # 2. Прокрутка до конца страницы
            print(f"   📜 Шаг 2: Прокрутка до конца страницы...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            
            # 3. Дополнительная прокрутка
            print(f"   📜 Шаг 3: Дополнительная прокрутка...")
            self.driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(0.3)
            
            # 4. Прокрутка с помощью клавиш (если возможно)
            print(f"   📜 Шаг 4: Прокрутка клавишами...")
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                for _ in range(3):
                    body.send_keys(Keys.PAGE_DOWN)
                    time.sleep(0.2)
            except Exception as e:
                print(f"   ⚠️ Ошибка прокрутки клавишами: {e}")
            
            # 5. Финальная прокрутка до конца
            print(f"   📜 Шаг 5: Финальная прокрутка...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.3)
            
            print(f"   ✅ Прокрутка завершена")
            
        except Exception as e:
            print(f"   ⚠️ Ошибка прокрутки: {e}")
            # Резервная прокрутка страницы
            try:
                print(f"   🔄 Резервная прокрутка...")
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(0.3)
            except Exception as e2:
                print(f"   ❌ Ошибка резервной прокрутки: {e2}")
    
    def scroll_page_fallback(self):
        """Резервная прокрутка всей страницы"""
        print("   🔄 Резервная прокрутка страницы...")
        
        initial_elements = self.count_business_elements()
        
        for i in range(10):  # Уменьшаем количество прокруток
            elements_before = self.count_business_elements()
            
            # Простая прокрутка страницы
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            elements_after = self.count_business_elements()
            
            if elements_after > elements_before:
                print(f"   ✅ Загружено: +{elements_after - elements_before}")
            else:
                print(f"   ⏳ Прокрутка {i + 1}: без изменений")
                if i >= 3:  # Прерываем раньше
                    break
        
        final_elements = self.count_business_elements()
        print(f"   📈 Итого элементов: {final_elements} (+{final_elements - initial_elements})")
    
    def count_business_elements(self):
        """Подсчет количества элементов предприятий на странице"""
        try:
            # Различные селекторы для подсчета элементов предприятий
            selectors = [
                "//a[contains(@href, '/org/')]",
                "//div[contains(@class, 'search-result-snippet-view')]",
                "//div[contains(@class, 'business-snippet-view')]",
                "//div[contains(@class, 'orgpage-snippet-view')]",
                "//div[contains(@class, 'snippet-view')]",
                "//div[contains(@class, 'search-result')]",
                "//div[contains(@class, 'business')]",
                "//div[contains(@class, 'org')]"
            ]
            
            max_count = 0
            best_selector = ""
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    count = len(elements)
                    if count > max_count:
                        max_count = count
                        best_selector = selector
                except:
                    continue
            
            if max_count > 0:
                print(f"   📊 Найдено {max_count} элементов (селектор: {best_selector})")
            
            return max_count
        except Exception as e:
            print(f"   ⚠️ Ошибка подсчета элементов: {e}")
            return 0
    
    
    def click_load_more_buttons(self):
        """Клик по кнопкам загрузки дополнительного контента"""
        try:
            # Специфичные селекторы для Яндекс.Карт
            button_selectors = [
                # Основные селекторы Яндекс.Карт
                "//button[contains(@class, 'search-list-view__load-more')]",
                "//button[contains(@class, 'load-more')]",
                "//button[contains(@class, 'show-more')]",
                "//button[contains(@class, 'more')]",
                "//button[contains(@class, 'load')]",
                "//button[contains(@class, 'show')]",
                "//button[contains(@class, 'button')]",
                # Селекторы по тексту
                "//button[contains(text(), 'Показать')]",
                "//button[contains(text(), 'Еще')]",
                "//button[contains(text(), 'Загрузить')]",
                "//button[contains(text(), 'Показать ещё')]",
                "//button[contains(text(), 'Показать еще')]",
                "//button[contains(text(), 'Загрузить еще')]",
                "//button[contains(text(), 'Показать все')]",
                # Селекторы для ссылок
                "//a[contains(text(), 'Показать')]",
                "//a[contains(text(), 'Еще')]",
                "//a[contains(@class, 'load-more')]",
                "//a[contains(@class, 'show-more')]",
                # Селекторы для div
                "//div[contains(@class, 'load-more')]",
                "//div[contains(@class, 'show-more')]",
                "//div[contains(@class, 'more')]",
                # Общие селекторы
                "//*[contains(@class, 'load-more')]",
                "//*[contains(@class, 'show-more')]",
                "//*[contains(@class, 'more')]"
            ]
            
            for selector in button_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        try:
                            if button.is_displayed() and button.is_enabled():
                                button_text = button.text.strip()
                                button_class = button.get_attribute('class')
                                
                                # Проверяем, что это действительно кнопка загрузки
                                if (button_text or 
                                    'load' in button_class.lower() or 
                                    'more' in button_class.lower() or 
                                    'show' in button_class.lower()):
                                    
                                    print(f"   🔘 Найдена кнопка загрузки: '{button_text}' (класс: {button_class})")
                                    
                                    # Пробуем разные способы клика
                                    try:
                                        button.click()
                                        print(f"   ✅ Клик выполнен обычным способом")
                                    except:
                                        try:
                                            self.driver.execute_script("arguments[0].click();", button)
                                            print(f"   ✅ Клик выполнен через JavaScript")
                                        except:
                                            try:
                                                self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", button)
                                                print(f"   ✅ Клик выполнен через событие")
                                            except:
                                                continue
                                    
                                    time.sleep(2)  # Уменьшаем время ожидания для оптимизации
                                    return True
                        except:
                            continue
                except:
                    continue
            
            return False
        except Exception as e:
            print(f"   ⚠️ Ошибка при поиске кнопок: {e}")
            return False
    
    def navigate_to_business(self, business_url):
        """Переход к карточке предприятия по прямой ссылке"""
        print(f"🎯 Переход к предприятию: {business_url}")
        
        try:
            # Проверяем на дубли
            if business_url in self.processed_urls:
                print("⚠️ Предприятие уже было обработано")
                return False
            
            self.processed_urls.add(business_url)
            
            # Переходим по ссылке
            self.driver.get(business_url)
            time.sleep(3)  # Уменьшаем время ожидания
            
            # Проверяем, что загрузилась карточка
            try:
                # Пробуем разные селекторы для проверки загрузки карточки
                card_selectors = [
                    "//div[contains(@class, 'business-card-view')]",
                    "//div[contains(@class, 'business-card')]",
                    "//div[contains(@class, 'orgpage')]",
                    "//div[contains(@class, 'business')]",
                    "//h1",  # Заголовок страницы
                    "//title"  # Заголовок в head
                ]
                
                card_loaded = False
                for selector in card_selectors:
                    try:
                        self.driver.implicitly_wait(2)
                        element = self.driver.find_element(By.XPATH, selector)
                        if element:
                            card_loaded = True
                            break
                    except:
                        continue
                
                if card_loaded:
                    print("✅ Карточка предприятия загружена")
                    return True
                else:
                    print("⚠️ Карточка не загрузилась")
                    return False
                    
            except Exception as e:
                print(f"⚠️ Ошибка проверки загрузки карточки: {e}")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка перехода к предприятию: {e}")
            return False
    
    def extract_business_data(self):
        """Извлечение данных из карточки предприятия"""
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
            'features': [],
            'accessibility': {},
            'has_panorama': False,
            'photos_count': 0,
            'stories': [],
            'coordinates': {'lat': '', 'lon': ''},
            'yandex_id': '',
            'url': self.driver.current_url,
            'last_updated': datetime.now().isoformat()
        }
        
        try:
            # НАЗВАНИЕ (из диагностики - рабочие селекторы)
            try:
                name_selectors = [
                    "//h1",  # Простой H1 - работает!
                    "//*[@itemprop='name']",  # Микроразметка - работает!
                    "//meta[@property='og:title']"  # Meta-тег в крайнем случае
                ]
                for selector in name_selectors:
                    try:
                        if 'meta' in selector:
                            name_elem = self.driver.find_element(By.XPATH, selector)
                            full_title = name_elem.get_attribute('content')
                            # Извлекаем только название до первой запятой
                            if full_title and ',' in full_title:
                                data['name'] = full_title.split(',')[0].strip()
                            elif full_title:
                                data['name'] = full_title.strip()
                        else:
                            name_elem = self.driver.find_element(By.XPATH, selector)
                            text = self.safe_get_text(name_elem)
                            if text:
                                data['name'] = text
                        
                        if data['name']:
                            break
                    except:
                        continue
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
                # Пробуем разные селекторы для категорий
                category_selectors = [
                    "//a[contains(@class, 'business-categories-view__category')]",
                    "//div[contains(@class, 'categories')]//a",
                    "//span[contains(@class, 'category')]"
                ]
                for selector in category_selectors:
                    try:
                        category_elements = self.driver.find_elements(By.XPATH, selector)
                        if category_elements:
                            data['categories'] = [self.safe_get_text(elem) for elem in category_elements if self.safe_get_text(elem)]
                            if data['categories']:
                                break
                    except:
                        continue
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
                address_selectors = [
                    "//div[contains(@class, 'business-contacts-view__address-link')]",
                    "//meta[@itemprop='address']",
                    "//div[contains(@class, 'business-contacts-view__address')]",
                    "//span[contains(@class, 'address')]"
                ]
                for selector in address_selectors:
                    try:
                        if 'meta' in selector:
                            address_elem = self.driver.find_element(By.XPATH, selector)
                            address_text = address_elem.get_attribute('content')
                        else:
                            address_elem = self.driver.find_element(By.XPATH, selector)
                            address_text = self.safe_get_text(address_elem)
                        
                        if address_text:
                            # Очищаем адрес от лишних элементов
                            address_text = address_text.replace('Маршрут', '').replace('Показать входы', '').replace('Маршру', '')
                            address_text = address_text.replace('Маршру', '').replace('Показать', '').replace('входы', '')
                            address_text = address_text.replace('  ', ' ').strip()
                            
                            # Дополнительная очистка от лишних символов
                            import re
                            address_text = re.sub(r'[^\w\s,.-]', '', address_text)  # Оставляем только буквы, цифры, пробелы, запятые, точки, дефисы
                            address_text = re.sub(r'\s+', ' ', address_text).strip()  # Убираем множественные пробелы
                            
                            if address_text and len(address_text) > 5:  # Минимальная длина адреса
                                data['address'] = address_text
                            break
                    except:
                        continue
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
            
            # ТОВАРЫ И ЦЕНЫ
            try:
                print("   🛍️ Извлечение товаров, услуг и меню...")
                
                # Ищем и переходим на вкладку товаров/услуг
                tab_found = False
                tab_selectors = [
                    "//div[@class='tabs-select-view__title _name_prices']",
                    "//div[@class='tabs-select-view__title _name_menu']",
                    "//div[contains(@class, 'tabs-select-view__title') and contains(text(), 'Цены')]",
                    "//div[contains(@class, 'tabs-select-view__title') and contains(text(), 'Товары')]",
                    "//div[contains(@class, 'tabs-select-view__title') and contains(text(), 'Услуги')]",
                    "//div[contains(@class, 'tabs-select-view__title') and contains(text(), 'Меню')]",
                    "//div[contains(@class, 'tab') and contains(text(), 'Цены')]",
                    "//div[contains(@class, 'tab') and contains(text(), 'Товары')]",
                    "//div[contains(@class, 'tab') and contains(text(), 'Услуги')]",
                    "//div[contains(@class, 'tab') and contains(text(), 'Меню')]",
                    "//a[contains(@href, 'prices')]",
                    "//a[contains(@href, 'menu')]",
                    "//a[contains(text(), 'Цены')]",
                    "//a[contains(text(), 'Товары')]",
                    "//a[contains(text(), 'Услуги')]",
                    "//a[contains(text(), 'Меню')]"
                ]
                
                for selector in tab_selectors:
                    try:
                        tab_elem = self.driver.find_element(By.XPATH, selector)
                        self.driver.execute_script("arguments[0].click();", tab_elem)
                        time.sleep(2)
                        print(f"   ✅ Перешли на вкладку товаров: {selector}")
                        tab_found = True
                        break
                    except:
                        continue
                
                if not tab_found:
                    print("   ⚠️ Вкладка товаров/услуг/меню не найдена, ищем на основной странице")
                
                # Агрессивная прокрутка для загрузки всех товаров/услуг/меню
                print("   📜 Прокрутка для загрузки товаров/услуг/меню...")
                for i in range(5):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    
                # Дополнительная прокрутка внутри возможных контейнеров
                try:
                    containers = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'scroll')]")
                    for container in containers:
                        for j in range(3):
                            self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight;", container)
                            time.sleep(0.5)
                except:
                    pass
                
                # Поиск товаров/услуг/меню - расширенные селекторы
                print("   🔍 Поиск элементов товаров/услуг/меню...")
                product_elems = []
                
                # Упрощенные селекторы для избежания зависания
                primary_selectors = [
                    "//div[contains(@class, 'business-full-items-grouped-view__item')]",
                    "//div[contains(@class, 'related-item-photo-view')]",
                    "//div[contains(@class, 'related-item-list-view__item')]", 
                    "//div[contains(@class, 'related-product-view')]",
                    "//div[contains(@class, 'product-item')]",
                    "//div[contains(@class, 'service-item')]",
                    "//div[contains(@class, 'price-item')]",
                    "//div[contains(@class, 'menu-item')]"
                ]
                
                for selector in primary_selectors:
                    try:
                        # Устанавливаем короткий таймаут для поиска
                        self.driver.implicitly_wait(2)
                        elems = self.driver.find_elements(By.XPATH, selector)
                        if elems:
                            product_elems = elems
                            print(f"   📊 Найдено товаров/услуг/меню с основным селектором '{selector}': {len(product_elems)}")
                            break
                    except:
                        continue
                    finally:
                        # Восстанавливаем таймаут
                        self.driver.implicitly_wait(10)
                
                # Если не нашли, пробуем дополнительные селекторы
                if not product_elems:
                    additional_selectors = [
                        "//div[contains(@class, 'menu-list-item')]",
                        "//div[contains(@class, 'menu-card')]",
                        "//div[contains(@class, 'menu-product')]",
                        "//div[contains(@class, 'menu-service')]",
                        "//div[contains(@class, 'menu-dish')]",
                        "//div[contains(@class, 'menu-category')]"
                    ]
                    
                    for selector in additional_selectors:
                        try:
                            # Устанавливаем короткий таймаут для поиска
                            self.driver.implicitly_wait(2)
                            elems = self.driver.find_elements(By.XPATH, selector)
                            if elems:
                                product_elems = elems
                                print(f"   📊 Найдено товаров/услуг/меню с доп. селектором '{selector}': {len(product_elems)}")
                                break
                        except:
                            continue
                        finally:
                            # Восстанавливаем таймаут
                            self.driver.implicitly_wait(10)
                    
                # Убираем fallback селекторы для избежания зависания
                
                # Обрабатываем найденные товары
                if not product_elems:
                    print("   ❌ Товары/услуги/меню не найдены")
                    data['products'] = []
                else:
                    print(f"   📊 Обрабатываем {len(product_elems)} товаров/услуг/меню...")
                    
                    # Ограничиваем количество товаров для избежания зависания
                    max_products = 20
                    if len(product_elems) > max_products:
                        print(f"   ⚠️ Ограничиваем до {max_products} товаров/услуг/меню (было {len(product_elems)})")
                        product_elems = product_elems[:max_products]
                    
                    products = []
                    for i, elem in enumerate(product_elems, 1):
                        try:
                            # Показываем прогресс каждые 5 товаров для лучшего контроля
                            if i % 5 == 0:
                                print(f"   📊 Обработано товаров/услуг/меню: {i}/{len(product_elems)}")
                            
                            # Проверяем, что элемент все еще доступен (мягкая проверка)
                            try:
                                # Пробуем получить текст элемента для проверки доступности
                                elem.text
                            except:
                                try:
                                    # Если не получается получить текст, пробуем is_displayed
                                    elem.is_displayed()
                                except:
                                    print(f"   ⚠️ Элемент {i} недоступен, пропускаем")
                                    continue
                            
                            # Устанавливаем общий таймаут для обработки товара
                            start_time = time.time()
                            max_processing_time = 10  # максимум 10 секунд на товар
                        
                            # Название - упрощенные селекторы
                            title = ""
                            title_selectors = [
                                ".//div[contains(@class, 'title')]",
                                ".//span[contains(@class, 'title')]",
                                ".//div[contains(@class, 'name')]",
                                ".//span[contains(@class, 'name')]",
                                ".//h3", ".//h4", ".//h5",
                                ".//a[contains(@class, 'title')]",
                                ".//div[@title]"
                            ]
                        
                            for selector in title_selectors:
                                try:
                                    # Устанавливаем короткий таймаут для поиска элемента
                                    self.driver.implicitly_wait(1)
                                    title_elem = elem.find_element(By.XPATH, selector)
                                    title = self.safe_get_text(title_elem)
                                    if title and len(title) > 2:
                                        break
                                except:
                                    continue
                                finally:
                                    # Восстанавливаем таймаут
                                    self.driver.implicitly_wait(10)
                        
                            # Цена - упрощенные селекторы
                            price = ""
                            price_selectors = [
                                ".//span[contains(@class, 'price')]",
                                ".//div[contains(@class, 'price')]",
                                ".//span[contains(@class, 'cost')]",
                                ".//div[contains(@class, 'cost')]",
                                ".//span[contains(@class, '₽')]",
                                ".//span[contains(@class, 'rub')]",
                                ".//div[contains(@class, 'rub')]"
                            ]
                        
                            for selector in price_selectors:
                                try:
                                    # Устанавливаем короткий таймаут для поиска элемента
                                    self.driver.implicitly_wait(1)
                                    price_elem = elem.find_element(By.XPATH, selector)
                                    price = self.safe_get_text(price_elem)
                                    if price:
                                        break
                                except:
                                    continue
                                finally:
                                    # Восстанавливаем таймаут
                                    self.driver.implicitly_wait(10)
                        
                            # Описание - упрощенные селекторы
                            description = ""
                            desc_selectors = [
                                ".//div[contains(@class, 'description')]",
                                ".//span[contains(@class, 'description')]",
                                ".//div[contains(@class, 'desc')]",
                                ".//span[contains(@class, 'desc')]",
                                ".//div[contains(@class, 'info')]",
                                ".//span[contains(@class, 'info')]"
                            ]
                        
                            for selector in desc_selectors:
                                try:
                                    # Устанавливаем короткий таймаут для поиска элемента
                                    self.driver.implicitly_wait(1)
                                    desc_elem = elem.find_element(By.XPATH, selector)
                                    description = self.safe_get_text(desc_elem)
                                    if description and len(description) > 5:
                                        break
                                except:
                                    continue
                                finally:
                                    # Восстанавливаем таймаут
                                    self.driver.implicitly_wait(10)
                        
                            # Проверяем время обработки
                            processing_time = time.time() - start_time
                            if processing_time > max_processing_time:
                                print(f"   ⚠️ Товар/услуга/меню {i} обрабатывается слишком долго ({processing_time:.1f}с), пропускаем")
                                continue
                            
                            # Добавляем товар если есть название или хотя бы цена
                            if (title and len(title) > 2) or (price and len(price) > 2):
                                # Если нет названия, но есть цена, создаем название
                                if not title or len(title) <= 2:
                                    title = f"Товар/услуга {i}"
                                
                                product_data = {
                                    'name': title,
                                    'price': price if price else 'Цена не указана',
                                    'description': description
                                }
                                products.append(product_data)
                            
                        except Exception as e:
                            if i <= 5:  # Показываем ошибки только для первых 5 товаров
                                print(f"   ⚠️ Ошибка обработки товара/услуги/меню {i}: {e}")
                            continue
                    
                    data['products'] = products
                    print(f"   🛍️ Извлечено товаров/услуг/меню: {len(products)}")
                
            except Exception as e:
                print(f"   ⚠️ Ошибка извлечения товаров/услуг/меню: {e}")
                data['products'] = []
            
            # ОСОБЕННОСТИ
            try:
                feature_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'business-features-view__bool-text')]")
                data['features'] = [self.safe_get_text(elem) for elem in feature_elements if self.safe_get_text(elem)]
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
    
    def parse(self, url):
        """Основной метод парсинга"""
        print("🚀 Запуск финального парсера Яндекс.Карт")
        print("=" * 60)
        print(f"🎯 ЦЕЛЬ: {self.target_count} предприятий")
        print("=" * 60)
        
        # Проверяем URL
        if not url or not isinstance(url, str):
            print(f"❌ Неверный URL: {url}")
            return False
        
        if not self.setup_driver():
            return False
        
        if not self.navigate_to_search(url):
            return False
        
        # Получаем ссылки на предприятия
        business_links = self.get_business_links()
        if not business_links:
            print("❌ Не найдены ссылки на предприятия")
            return False
        
        print(f"\n📊 НАЙДЕНО {len(business_links)} ССЫЛОК НА ПРЕДПРИЯТИЯ")
        print(f"🎯 ЗАПРОШЕНО: {self.target_count if self.target_count > 0 else 'ВСЕ НАЙДЕННЫЕ'} предприятий")
        
        # Ограничиваем до нужного количества (0 = все найденные)
        if self.target_count > 0:
            target_links = business_links[:self.target_count]
        else:
            target_links = business_links  # Все найденные
            
        print(f"📊 ОБРАБАТЫВАЕМ {len(target_links)} ПРЕДПРИЯТИЙ")
        print("=" * 60)
        
        # Обрабатываем каждое предприятие
        for i, business_url in enumerate(target_links):
            print(f"\n📍 Предприятие {i+1}/{len(target_links)}")
            
            if self.navigate_to_business(business_url):
                business_data = self.extract_business_data()
                
                if business_data and business_data['name']:
                    self.businesses.append(business_data)
                    print(f"✅ Обработано {i+1}/{len(target_links)}: {business_data['name']}")
                    print(f"   📞 Телефонов: {len(business_data['phones'])}")
                    print(f"   🏷️ Категорий: {len(business_data['categories'])}")
                    print(f"   🛍️ Товаров: {len(business_data['products'])}")
                    print(f"   ⭐ Рейтинг: {business_data['rating']}")
                else:
                    print("⚠️ Данные не извлечены")
            else:
                print("❌ Не удалось открыть предприятие")
            
            time.sleep(2)  # Пауза между предприятиями
        
        print(f"\n📈 ПАРСИНГ ЗАВЕРШЕН!")
        print(f"✅ Успешно обработано: {len(self.businesses)} из {len(target_links)}")
        
        if self.target_count > 0:
            print(f"🎯 Цель ({self.target_count}): {'ДОСТИГНУТА' if len(self.businesses) >= self.target_count else 'НЕ ДОСТИГНУТА'}")
        else:
            print(f"🎯 Цель (ВСЕ НАЙДЕННЫЕ): {'ДОСТИГНУТА' if len(self.businesses) == len(target_links) else 'ЧАСТИЧНО ДОСТИГНУТА'}")
            
        return True
    
    def save_results(self, project_name=None):
        """Сохранение результатов"""
        if not self.businesses:
            print("❌ Нет данных для сохранения")
            return
        
        os.makedirs("output", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Используем имя проекта или временную метку
        if project_name:
            base_name = project_name
        else:
            base_name = f"final_data_{timestamp}"
        
        # JSON с полными данными
        json_filename = f"output/{base_name}.json"
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
                'Услуги': ', '.join(business['services'][:3]),  # Первые 3 услуги
                'Товары': len(business['products']),
                'Панорама': 'Да' if business['has_panorama'] else 'Нет',
                'Истории': len(business['stories']),
                'URL': business['url'],
                'Yandex ID': business['yandex_id']
            }
            excel_data.append(row)
        
        excel_filename = f"output/{base_name}_businesses.xlsx"
        df = pd.DataFrame(excel_data)
        df.to_excel(excel_filename, index=False)
        print(f"📊 Основные данные: {excel_filename}")
        
        # Создаем клиентский HTML дашборд автоматически
        try:
            print("\n🌐 Создание клиентского HTML дашборда...")
            from client_dashboard_generator import ClientDashboardGenerator
            generator = ClientDashboardGenerator()
            dashboard_file = generator.generate_dashboard(json_filename, project_name=project_name)
            if dashboard_file:
                print(f"✅ Клиентский дашборд создан: {dashboard_file}")
                print(f"📁 Дашборд размещен в папке проекта: {os.path.dirname(dashboard_file)}")
                print(f"🌐 Откройте в браузере: {os.path.abspath(dashboard_file)}")
                print(f"📊 Проект: {project_name if project_name else 'Без названия'}")
            else:
                print("❌ Не удалось создать дашборд")
        except ImportError as e:
            print(f"❌ Ошибка импорта клиентского генератора дашборда: {e}")
            print("Убедитесь, что файл client_dashboard_generator.py находится в той же папке")
            # Пробуем современный генератор как fallback
            try:
                print("🔄 Пробуем современный генератор дашборда...")
                from modern_dashboard_generator import ModernDashboardGenerator
                generator = ModernDashboardGenerator()
                dashboard_file = generator.generate_dashboard(json_filename)
                if dashboard_file:
                    print(f"✅ Современный дашборд создан: {dashboard_file}")
            except:
                print("❌ Не удалось создать дашборд")
        except Exception as e:
            print(f"❌ Ошибка создания дашборда: {e}")
            import traceback
            traceback.print_exc()
        
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
    url = "https://yandex.ru/maps/39/rostov-na-donu/search/Ростов%20на%20дону%20суворовский%20стоматология/?ll=39.806284%2C47.275656&sctx=ZAAAAAgCEAAaKAoSCbnEkQci10NAESl4CrlSn0dAEhIJ98ySADW1zj8R1lJA2v8Aqz8iBgABAgMEBSgKOABA0YgGSAFqAnJ1nQHNzMw9oAEAqAEAvQHFGEBwwgElzKy6tfoGxpeW5AXL5fTcA9Ka8PoDwpzMogT4sL%2FgA%2Fyw57rlBoICStCg0L7RgdGC0L7QsiDQvdCwINC00L7QvdGDINGB0YPQstC%2B0YDQvtCy0YHQutC40Lkg0YHRgtC%2B0LzQsNGC0L7Qu9C%2B0LPQuNGPigIAkgICMzmaAgxkZXNrdG9wLW1hcHPaAigKEgnfWbvtQuFDQBGw%2Fs8gd6FHQBISCYBnXaPlQN0%2FEQA8uDtrt7k%2F4AIB&sll=39.806284%2C47.275656&sspn=0.914172%2C0.200856&z=10.61"
    
    target_count = TARGET_BUSINESSES_COUNT  # Используем значение из конфигурации
    
    parser = FinalWorkingParser(target_count=target_count)
    
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
