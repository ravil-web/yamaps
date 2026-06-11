#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
from datetime import datetime
from config import *
from single_business_parser import SingleBusinessParser
from client_dashboard import ClientDashboardGenerator
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class FixedMainParser:
    def __init__(self):
        self.driver = None
        self.setup_logging()
        self.setup_folders()
        
    def setup_logging(self):
        """Настройка системы логирования"""
        os.makedirs(f"{FOLDER_STRUCTURE['base_folder']}/{FOLDER_STRUCTURE['logs_subfolder']}", exist_ok=True)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Файловый обработчик
        log_filename = f"{FOLDER_STRUCTURE['base_folder']}/{FOLDER_STRUCTURE['logs_subfolder']}/fixed_parser_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_filename, encoding=LOGGING['file_encoding'])
        file_handler.setLevel(getattr(logging, LOGGING['level']))
        file_handler.setFormatter(formatter)
        
        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Настройка логгера
        self.logger = logging.getLogger('FixedMainParser')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info("🚀 Система логирования инициализирована")
        
    def setup_folders(self):
        """Создание структуры папок"""
        try:
            os.makedirs(FOLDER_STRUCTURE['base_folder'], exist_ok=True)
            businesses_folder = f"{FOLDER_STRUCTURE['base_folder']}/{FOLDER_STRUCTURE['businesses_subfolder']}"
            os.makedirs(businesses_folder, exist_ok=True)
            logs_folder = f"{FOLDER_STRUCTURE['base_folder']}/{FOLDER_STRUCTURE['logs_subfolder']}"
            os.makedirs(logs_folder, exist_ok=True)
            self.logger.info("📁 Структура папок создана")
        except Exception as e:
            self.logger.error(f"❌ Ошибка создания папок: {e}")
            
    def setup_driver(self):
        """Инициализация WebDriver"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument(f'--window-size={BROWSER_OPTIONS["window_size"]}')
        
        if BROWSER_OPTIONS['start_maximized']:
            options.add_argument('--start-maximized')
            
        if BROWSER_OPTIONS['disable_logging']:
            options.add_argument('--disable-logging')
            options.add_argument(f'--log-level={BROWSER_OPTIONS["log_level"]}')
        
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
            
    def switch_to_list_view(self):
        """Переключение на режим списка"""
        self.logger.info("🔄 Попытка переключения на режим списка...")
        
        # Селекторы кнопки переключения в список
        list_view_selectors = [
            "//button[contains(@class, 'list-view-toggle')]",
            "//button[contains(@class, 'tabs-select-view__tab') and contains(@aria-label, 'Список')]",
            "//button[contains(@title, 'Список')]",
            "//button[contains(text(), 'Список')]",
            "//div[contains(@class, 'tabs-select-view')]//button[2]",  # Вторая кнопка в табах
            "//button[contains(@class, 'map-list-toggle')]",
            "//div[contains(@class, 'search-tabs')]//button[contains(text(), 'Список')]",
            "//div[contains(@class, 'toggle')]//button[contains(@aria-label, 'Список')]"
        ]
        
        for selector in list_view_selectors:
            try:
                self.logger.info(f"🔍 Проверяем селектор: {selector}")
                wait = WebDriverWait(self.driver, 3)
                button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                
                if button.is_displayed() and button.is_enabled():
                    self.logger.info(f"✅ Найдена кнопка списка: {selector}")
                    self.driver.execute_script("arguments[0].click();", button)
                    time.sleep(3)
                    self.logger.info("🔄 Кнопка списка нажата")
                    return True
                    
            except Exception as e:
                self.logger.debug(f"❌ Селектор не сработал: {selector} - {e}")
                continue
        
        # Альтернативный способ - поиск по тексту во всех кнопках
        try:
            self.logger.info("🔍 Поиск кнопки списка по тексту...")
            buttons = self.driver.find_elements(By.XPATH, "//button")
            for button in buttons:
                try:
                    text = button.get_attribute("textContent") or ""
                    aria_label = button.get_attribute("aria-label") or ""
                    title = button.get_attribute("title") or ""
                    
                    if any(word in (text + aria_label + title).lower() for word in ['список', 'list']):
                        if button.is_displayed() and button.is_enabled():
                            self.logger.info(f"✅ Найдена кнопка списка по тексту: '{text}' / '{aria_label}' / '{title}'")
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(3)
                            return True
                except:
                    continue
        except Exception as e:
            self.logger.debug(f"❌ Поиск по тексту не удался: {e}")
        
        self.logger.warning("⚠️ Кнопка переключения в список не найдена")
        return False
    
    def extract_business_urls(self):
        """Извлечение URL предприятий со страницы поиска"""
        business_urls = []
        try:
            self.logger.info("🔍 Поиск предприятий...")
            self.logger.info(f"📄 URL поиска: {SEARCH_URL}")
            
            self.driver.get(SEARCH_URL)
            time.sleep(DELAYS['page_load'])
            
            # Попытка переключиться на режим списка
            self.switch_to_list_view()
            time.sleep(2)
            
            # Сохраняем HTML для анализа
            with open('current_page_debug.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            self.logger.info("💾 HTML сохранен в current_page_debug.html")
            
            # Новые селекторы для поиска элементов списка
            business_selectors = [
                # Современные селекторы для списка предприятий
                "//div[contains(@class, 'search-snippet-view')]",
                "//li[contains(@class, 'search-snippet-view')]",
                "//div[contains(@class, 'business-snippet-view')]",
                "//div[contains(@class, 'search-business-snippet-view')]",
                "//li[contains(@class, 'serp-item')]",
                "//div[contains(@class, 'companies-list-item')]",
                "//div[contains(@class, 'search-result-item')]",
                # Селекторы для элементов карты (если список недоступен)
                "//div[contains(@class, 'search-placemark-view')]",
                "//ymaps[contains(@class, 'marker')]//div[contains(@class, 'search-placemark-view')]"
            ]
            
            self.logger.info("🔍 Поиск элементов предприятий...")
            
            business_elements = []
            working_selector = None
            
            for selector in business_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    self.logger.info(f"📊 Селектор '{selector}': {len(elements)} элементов")
                    
                    if elements and len(elements) > len(business_elements):
                        business_elements = elements
                        working_selector = selector
                        self.logger.info(f"✅ Лучший селектор: {working_selector} ({len(elements)} элементов)")
                        
                except Exception as e:
                    self.logger.debug(f"❌ Ошибка с селектором '{selector}': {e}")
                    continue
            
            # Если не найдено элементов списка, пробуем прокрутку и повторный поиск
            if not business_elements:
                self.logger.info("📜 Элементы не найдены, выполняем прокрутку...")
                self.perform_scrolling()
                
                # Повторный поиск после прокрутки
                for selector in business_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        if elements:
                            business_elements = elements
                            working_selector = selector
                            self.logger.info(f"✅ После прокрутки найдено: {len(elements)} элементов")
                            break
                    except:
                        continue
            
            if not business_elements:
                self.logger.error("❌ Не найдено элементов предприятий")
                return []
            
            # Извлечение URL из найденных элементов
            self.logger.info(f"🔗 Извлечение URL из {len(business_elements)} элементов...")
            
            # Селекторы для поиска ссылок внутри элементов
            link_selectors = [
                ".//a[contains(@class, 'link-overlay')]",
                ".//a[contains(@href, '/org/')]",
                ".//a[contains(@class, 'business-link')]",
                ".//a[@href]"
            ]
            
            unique_urls = set()
            
            for i, element in enumerate(business_elements):
                try:
                    url_found = False
                    
                    # Пробуем найти ссылку внутри элемента
                    for link_sel in link_selectors:
                        try:
                            links = element.find_elements(By.XPATH, link_sel)
                            for link in links:
                                href = link.get_attribute('href')
                                if href and '/org/' in href and '/gallery/' not in href and '/reviews/' not in href:
                                    clean_url = href.split('?')[0].split('#')[0]
                                    if not clean_url.endswith('/'):
                                        clean_url += '/'
                                    
                                    if clean_url not in unique_urls:
                                        unique_urls.add(clean_url)
                                        business_urls.append(clean_url)
                                        self.logger.info(f"   ✅ URL {len(business_urls)}: {clean_url}")
                                        url_found = True
                                        break
                            if url_found:
                                break
                        except:
                            continue
                    
                    # Если ссылка не найдена, попробуем кликнуть по элементу
                    if not url_found:
                        try:
                            self.logger.info(f"🖱️ Пробуем кликнуть по элементу {i+1}")
                            original_url = self.driver.current_url
                            
                            # Клик по элементу
                            self.driver.execute_script("arguments[0].click();", element)
                            time.sleep(2)
                            
                            # Проверяем, изменился ли URL
                            new_url = self.driver.current_url
                            if new_url != original_url and '/org/' in new_url:
                                clean_url = new_url.split('?')[0].split('#')[0]
                                if not clean_url.endswith('/'):
                                    clean_url += '/'
                                
                                if clean_url not in unique_urls:
                                    unique_urls.add(clean_url)
                                    business_urls.append(clean_url)
                                    self.logger.info(f"   ✅ URL {len(business_urls)} (клик): {clean_url}")
                                
                                # Возвращаемся назад
                                self.driver.back()
                                time.sleep(2)
                        except:
                            pass
                    
                    # Останавливаемся, если достигли целевого количества
                    if TARGET_BUSINESSES_COUNT > 0 and len(business_urls) >= TARGET_BUSINESSES_COUNT:
                        self.logger.info(f"🎯 Достигнуто целевое количество: {TARGET_BUSINESSES_COUNT}")
                        break
                        
                except Exception as e:
                    self.logger.debug(f"❌ Ошибка обработки элемента {i+1}: {e}")
                    continue
            
            # Если URL мало, пробуем дополнительную прокрутку
            if len(business_urls) < TARGET_BUSINESSES_COUNT:
                self.logger.info(f"⚠️ Найдено {len(business_urls)} URL, нужно {TARGET_BUSINESSES_COUNT}")
                self.logger.info("📜 Выполняем дополнительную прокрутку...")
                
                self.perform_extended_scrolling()
                
                # Повторный поиск элементов
                new_elements = self.driver.find_elements(By.XPATH, working_selector) if working_selector else []
                self.logger.info(f"📊 После дополнительной прокрутки: {len(new_elements)} элементов")
                
                # Обработка новых элементов
                for element in new_elements[len(business_elements):]:
                    try:
                        for link_sel in link_selectors:
                            try:
                                links = element.find_elements(By.XPATH, link_sel)
                                for link in links:
                                    href = link.get_attribute('href')
                                    if href and '/org/' in href:
                                        clean_url = href.split('?')[0].split('#')[0]
                                        if not clean_url.endswith('/'):
                                            clean_url += '/'
                                        
                                        if clean_url not in unique_urls:
                                            unique_urls.add(clean_url)
                                            business_urls.append(clean_url)
                                            self.logger.info(f"   ✅ Доп. URL {len(business_urls)}: {clean_url}")
                                            break
                                if len(business_urls) >= TARGET_BUSINESSES_COUNT:
                                    break
                            except:
                                continue
                        if len(business_urls) >= TARGET_BUSINESSES_COUNT:
                            break
                    except:
                        continue
            
            self.logger.info(f"✅ Извлечено URL предприятий: {len(business_urls)}")
            return business_urls
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения URL предприятий: {e}")
            return []
    
    def perform_scrolling(self):
        """Базовая прокрутка страницы"""
        self.logger.info("📜 Выполняем базовую прокрутку...")
        
        for i in range(5):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            self.driver.execute_script("window.scrollBy(0, -500);")
            time.sleep(1)
            self.driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(1)
    
    def perform_extended_scrolling(self):
        """Расширенная прокрутка с поиском кнопок загрузки"""
        self.logger.info("📜 Выполняем расширенную прокрутку...")
        
        for scroll_round in range(10):
            # Прокрутка до низа
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Поиск кнопок "Показать еще"
            show_more_selectors = [
                "//button[contains(text(), 'Показать еще')]",
                "//button[contains(text(), 'Загрузить еще')]",
                "//button[contains(text(), 'Еще')]",
                "//a[contains(text(), 'Показать еще')]",
                "//div[contains(@class, 'show-more')]//button",
                "//div[contains(@class, 'load-more')]//button"
            ]
            
            button_clicked = False
            for selector in show_more_selectors:
                try:
                    buttons = self.driver.find_elements(By.XPATH, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            self.logger.info(f"🔘 Нажимаем кнопку: {selector}")
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(3)
                            button_clicked = True
                            break
                    if button_clicked:
                        break
                except:
                    continue
            
            if not button_clicked:
                # Простая прокрутка
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(1)
    
    def parse_businesses(self, business_urls):
        """Парсинг списка предприятий"""
        results = []
        successful_count = 0
        failed_count = 0
        
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"🚀 НАЧАЛО ПАРСИНГА {len(business_urls)} ПРЕДПРИЯТИЙ")
        self.logger.info(f"{'='*80}")
        
        for i, business_url in enumerate(business_urls, 1):
            self.logger.info(f"\n🔄 ПРЕДПРИЯТИЕ {i}/{len(business_urls)}")
            self.logger.info(f"📄 URL: {business_url}")
            
            try:
                # Создание парсера для одного предприятия
                single_parser = SingleBusinessParser()
                
                # Передаем существующий WebDriver
                single_parser.driver = self.driver
                single_parser._external_driver = True
                
                # Настройка лимита товаров
                if TARGET_PRODUCTS_COUNT > 0:
                    single_parser.max_products = TARGET_PRODUCTS_COUNT
                
                # Парсинг предприятия
                business_data = single_parser.parse_single_business(business_url)
                
                if business_data:
                    results.append(business_data)
                    successful_count += 1
                    self.logger.info(f"✅ Предприятие {i} - УСПЕШНО")
                else:
                    failed_count += 1
                    self.logger.error(f"❌ Предприятие {i} - НЕ УДАЛОСЬ")
                    
            except Exception as e:
                failed_count += 1
                self.logger.error(f"❌ Критическая ошибка предприятия {i}: {e}")
                
                if not ERROR_HANDLING['continue_on_error']:
                    self.logger.error("🛑 Парсинг остановлен из-за ошибки")
                    break
                    
            # Задержка между предприятиями
            if i < len(business_urls):
                self.logger.info(f"⏳ Ожидание {DELAYS['between_businesses']} сек...")
                time.sleep(DELAYS['between_businesses'])
                
        # Итоговая статистика
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"🎉 ПАРСИНГ ЗАВЕРШЕН")
        self.logger.info(f"{'='*80}")
        self.logger.info(f"📊 Статистика:")
        self.logger.info(f"   ✅ Успешно: {successful_count}")
        self.logger.info(f"   ❌ Неудачно: {failed_count}")
        self.logger.info(f"   📄 Всего: {len(business_urls)}")
        
        return results
        
    def save_summary(self, results):
        """Сохранение сводного отчета"""
        try:
            summary_file = f"{FOLDER_STRUCTURE['base_folder']}/summary_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("СВОДНЫЙ ОТЧЕТ ИСПРАВЛЕННОГО ПАРСИНГА\n")
                f.write("="*80 + "\n")
                f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"URL поиска: {SEARCH_URL}\n")
                f.write(f"Целевое количество предприятий: {TARGET_BUSINESSES_COUNT}\n")
                f.write(f"Целевое количество товаров: {TARGET_PRODUCTS_COUNT}\n")
                f.write(f"Обработано предприятий: {len(results)}\n")
                f.write("\n" + "="*80 + "\n")
                f.write("ДЕТАЛЬНАЯ ИНФОРМАЦИЯ:\n")
                f.write("="*80 + "\n")
                
                for i, business in enumerate(results, 1):
                    f.write(f"\n{i}. {business.get('name', 'N/A')}\n")
                    f.write(f"   URL: {business.get('url', 'N/A')}\n")
                    f.write(f"   Адрес: {business.get('address', 'N/A')}\n")
                    f.write(f"   Рейтинг: {business.get('rating', 'N/A')}\n")
                    f.write(f"   Телефоны: {len(business.get('phones', []))}\n")
                    f.write(f"   Товары/услуги: {len(business.get('products_and_services', []))}\n")
                    
            self.logger.info(f"📄 Сводный отчет сохранен: {summary_file}")
            
            # Создаем дашборд сразу после сохранения отчета
            self.create_dashboard()
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка сохранения сводного отчета: {e}")
            
    def create_dashboard(self):
        """Автоматическое создание клиентского дашборда"""
        try:
            self.logger.info("📊 Создание клиентского дашборда...")
            dashboard_generator = ClientDashboardGenerator()
            dashboard_file = dashboard_generator.generate_html_dashboard()
            self.logger.info(f"✅ Дашборд создан: {dashboard_file}")
            self.logger.info("🌐 Откройте файл в браузере для просмотра")
        except Exception as e:
            self.logger.error(f"❌ Ошибка создания дашборда: {e}")
            
    def run(self):
        """Основной метод запуска парсера"""
        try:
            self.logger.info("🚀 ЗАПУСК ИСПРАВЛЕННОГО ПАРСЕРА")
            self.logger.info("="*60)
            
            # Инициализация WebDriver
            if not self.setup_driver():
                return False
                
            # Извлечение URL предприятий
            business_urls = self.extract_business_urls()
            if not business_urls:
                self.logger.error("❌ Не найдено предприятий для парсинга")
                return False
                
            # Парсинг предприятий
            results = self.parse_businesses(business_urls)
            
            # Сохранение сводного отчета (включает создание дашборда)
            self.save_summary(results)
            
            self.logger.info("🎉 ПАРСИНГ ЗАВЕРШЕН УСПЕШНО")
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
    print("🚀 ЗАПУСК ИСПРАВЛЕННОГО ПАРСЕРА YANDEX MAPS")
    print("="*60)
    print(f"📄 URL поиска: {SEARCH_URL}")
    print(f"🎯 Целевое количество предприятий: {TARGET_BUSINESSES_COUNT}")
    print(f"🛍️ Целевое количество товаров: {TARGET_PRODUCTS_COUNT}")
    print("="*60)
    
    parser = FixedMainParser()
    success = parser.run()
    
    if success:
        print("\n✅ Парсинг завершен успешно!")
        print("📊 Клиентский дашборд создан автоматически!")
    else:
        print("\n❌ Парсинг завершен с ошибками!")
        
    print(f"\n📁 Результаты сохранены в папке: {FOLDER_STRUCTURE['base_folder']}")
    print("🌐 Откройте файл client_dashboard_*.html в браузере для просмотра дашборда")


if __name__ == "__main__":
    main()
