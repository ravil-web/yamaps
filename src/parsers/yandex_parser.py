#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.config import *
from .single_parser import SingleBusinessParser
from src.dashboard.client_dashboard import ClientDashboardGenerator
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class MainParser:
    def __init__(self, session_name=None):
        self.session_name = session_name or f"parsing_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session_folder = None
        self.driver = None
        self.setup_session_folder()
        self.setup_logging()
        self.setup_folders()
        self.setup_driver()
    
    def setup_session_folder(self):
        """Создание папки для текущей сессии парсинга"""
        # Создаем главную папку результатов
        os.makedirs(FOLDER_STRUCTURE['base_folder'], exist_ok=True)
        
        # Создаем папку для этой сессии
        self.session_folder = f"{FOLDER_STRUCTURE['base_folder']}/{self.session_name}"
        os.makedirs(self.session_folder, exist_ok=True)
        
        # Создаем подпапки внутри сессии
        os.makedirs(f"{self.session_folder}/businesses", exist_ok=True)
        os.makedirs(f"{self.session_folder}/logs", exist_ok=True)
        
        print(f"📁 Создана папка сессии: {self.session_folder}")
        
    def setup_logging(self):
        """Настройка системы логирования"""
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Файловый обработчик - сохраняем в папку сессии
        log_filename = f"{self.session_folder}/logs/main_parser_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_filename, encoding=LOGGING['file_encoding'])
        file_handler.setLevel(getattr(logging, LOGGING['level']))
        file_handler.setFormatter(formatter)
        
        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Настройка логгера
        self.logger = logging.getLogger('MainParser')
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info("🚀 Система логирования инициализирована")
        
    def setup_folders(self):
        """Создание структуры папок"""
        try:
            # Основная папка
            os.makedirs(FOLDER_STRUCTURE['base_folder'], exist_ok=True)
            
            # Папка для предприятий
            businesses_folder = f"{FOLDER_STRUCTURE['base_folder']}/{FOLDER_STRUCTURE['businesses_subfolder']}"
            os.makedirs(businesses_folder, exist_ok=True)
            
            # Папка для логов
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
            
            self.driver.implicitly_wait(10)
            self.logger.info("✅ WebDriver инициализирован успешно")
            return True
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации WebDriver: {e}")
            return False

    def extract_business_urls(self) -> List[str]:
        """Извлечение URL предприятий - РАБОЧИЙ МЕТОД из simple_working_parser"""
        business_urls: List[str] = []
        try:
            self.logger.info("🔍 Поиск предприятий...")
            self.logger.info(f"📄 URL поиска: {SEARCH_URL}")
            
            self.driver.get(SEARCH_URL)
            
            # Ожидание загрузки списка (оптимизация WebDriverWait)
            try:
                WebDriverWait(self.driver, DELAYS.get('page_load', 10)).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.search-list-view__list, div.search-snippet-view, div.scroll__container, div.search-tab-business"))
                )
            except TimeoutException:
                self.logger.warning("⚠️ Контейнер списка не появился вовремя")
            
            # УЛУЧШЕННАЯ прокрутка: ищем контейнер списка и скроллим его
            self.logger.info("📜 Поиск контейнера списка предприятий...")
            
            # Ищем контейнер списка предприятий
            scroll_container = None
            scroll_selectors = [
                "div.search-list-view__list",
                "div.search-snippet-view",
                "div.scroll__container",
                "div.search-tab-business"
            ]
            
            for selector in scroll_selectors:
                try:
                    containers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if containers:
                        scroll_container = containers[0]
                        self.logger.info(f"✅ Найден контейнер: {selector}")
                        break
                except:
                    continue
            
            self.logger.info("📜 Выполняем интенсивную прокрутку для загрузки всех предприятий...")
            
            # Метод 1: Прокрутка контейнера списка (если найден)
            if scroll_container:
                self.logger.info("🎯 Скроллим контейнер списка...")
                last_scroll_top = -1
                for scroll_round in range(30):
                    try:
                        # Скроллим контейнер
                        self.driver.execute_script("arguments[0].scrollTop += 1000;", scroll_container)
                        
                        # Ждем изменения прокрутки (вместо фиксированного sleep)
                        start_wait = time.time()
                        while time.time() - start_wait < 1.0:
                            current_scroll_top = self.driver.execute_script("return arguments[0].scrollTop;", scroll_container)
                            if current_scroll_top != last_scroll_top:
                                break
                            time.sleep(0.1)
                        
                        # Проверяем достигли ли дна
                        scroll_height = self.driver.execute_script("return arguments[0].scrollHeight;", scroll_container)
                        scroll_top = self.driver.execute_script("return arguments[0].scrollTop;", scroll_container)
                        client_height = self.driver.execute_script("return arguments[0].clientHeight;", scroll_container)
                        
                        if scroll_top + client_height >= scroll_height - 100:
                            self.logger.info("📜 Достигнут конец списка")
                            break
                        
                        if scroll_top == last_scroll_top:
                             # Если позиция не изменилась после попытки прокрутки и ожидания
                             self.logger.debug("📜 Позиция прокрутки не изменилась")
                        
                        last_scroll_top = scroll_top
                            
                        if scroll_round % 5 == 0:
                            self.logger.info(f"📜 Прокрутка контейнера: {scroll_round + 1}/30")
                            
                    except Exception as e:
                        self.logger.debug(f"Ошибка прокрутки контейнера: {e}")
                        break
            
            # Метод 2: Обычная прокрутка окна (дополнительно)
            self.logger.info("🌐 Дополнительная прокрутка окна...")
            last_page_height = self.driver.execute_script("return document.body.scrollHeight")
            for scroll_round in range(15):
                self.driver.execute_script("window.scrollBy(0, 800);")
                
                # Вместо жесткого sleep(1) ждем возможной подгрузки
                try:
                     WebDriverWait(self.driver, 1).until(
                         lambda d: d.execute_script("return document.body.scrollHeight") > last_page_height
                     )
                     last_page_height = self.driver.execute_script("return document.body.scrollHeight")
                except TimeoutException:
                     pass
                
                # Проверяем кнопку "Показать еще"
                try:
                    show_more_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Показать ещё') or contains(text(), 'Показать еще') or contains(@class, 'show-more')]")
                    for btn in show_more_buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            self.logger.info("🔄 Нажимаем 'Показать ещё'")
                            self.driver.execute_script("arguments[0].click();", btn)
                            # Ждем обновления контента
                            try:
                                WebDriverWait(self.driver, 5).until(
                                    lambda d: d.execute_script("return document.body.scrollHeight") > last_page_height
                                )
                                last_page_height = self.driver.execute_script("return document.body.scrollHeight")
                            except TimeoutException:
                                time.sleep(2) # Fallback
                            break
                except:
                    pass
                
                if scroll_round % 5 == 0:
                    self.logger.info(f"📜 Прокрутка окна: {scroll_round + 1}/15")
            
            # ПРАВИЛЬНЫЙ МЕТОД: Поиск точных ссылок card-title-view__title-link
            self.logger.info("🔍 Поиск ссылок card-title-view__title-link...")
            
            # Сначала ищем точные ссылки с правильным классом
            title_links = self.driver.find_elements(By.CSS_SELECTOR, "a.card-title-view__title-link[href*='/maps/org/']")
            self.logger.info(f"📊 Найдено ссылок card-title-view__title-link: {len(title_links)}")
            
            # Если не найдено, ищем все ссылки с /maps/org/
            if not title_links:
                self.logger.info("🔍 Поиск всех ссылок с /maps/org/...")
                title_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/maps/org/')]")
                self.logger.info(f"📊 Найдено всех ссылок с /maps/org/: {len(title_links)}")
            
            # Если и этого мало, ищем вообще все ссылки с /org/
            if len(title_links) < 5:
                self.logger.info("🔍 Поиск всех ссылок с /org/...")
                all_org_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/org/')]")
                title_links.extend(all_org_links)
                self.logger.info(f"📊 Общее количество ссылок: {len(title_links)}")
            
            # Фильтруем и собираем уникальные URL
            seen_urls = set()
            self.logger.info(f"🔍 Анализируем {len(title_links)} найденных ссылок...")
            
            for i, link in enumerate(title_links):
                try:
                    href = link.get_attribute('href')
                    self.logger.debug(f"Ссылка {i+1}: {href}")
                    
                    if href and '/org/' in href:
                        # Исключаем ссылки на отзывы, галереи и фото
                        if any(exclude in href for exclude in ['/reviews/', '/gallery/', '/photos/']):
                            self.logger.debug(f"❌ Исключаем: {href} (отзывы/галерея/фото)")
                            continue
                        
                        # Если это относительная ссылка, делаем её абсолютной
                        if href.startswith('/maps/org/'):
                            clean_url = f"https://yandex.ru{href}"
                        else:
                            clean_url = href
                        
                        # Очищаем URL от параметров
                        clean_url = clean_url.split('?')[0].split('#')[0]
                        if not clean_url.endswith('/'):
                            clean_url += '/'
                        
                        if clean_url in seen_urls:
                            self.logger.debug(f"❌ Дубль: {clean_url}")
                            continue
                        
                        seen_urls.add(clean_url)
                        business_urls.append(clean_url)
                        
                        # Пробуем получить название для лога
                        try:
                            name = link.text.strip() or "Без названия"
                            if len(name) > 50:  # Обрезаем длинные названия
                                name = name[:50] + "..."
                        except:
                            name = "Без названия"
                        
                        self.logger.info(f"   ✅ {len(business_urls)}. {name} - {clean_url}")
                        
                        # Останавливаемся при достижении цели
                        if TARGET_BUSINESSES_COUNT > 0 and len(business_urls) >= TARGET_BUSINESSES_COUNT:
                            self.logger.info(f"🎯 Достигнуто целевое количество: {TARGET_BUSINESSES_COUNT}")
                            break
                            
                except Exception as e:
                    self.logger.debug(f"❌ Ошибка обработки ссылки {i+1}: {e}")
                    continue
            
            # Если найдено мало ссылок, пробуем клики по элементам (дополнительный метод)
            if len(business_urls) < TARGET_BUSINESSES_COUNT and len(business_urls) < 15:
                self.logger.info("🖱️ Мало ссылок, пробуем клики по элементам...")
                clickable_elements = self.driver.find_elements(By.XPATH, "//*[contains(@data-id, '') or contains(@class, 'placemark') or contains(@class, 'marker')]")
                self.logger.info(f"📊 Найдено кликабельных элементов: {len(clickable_elements)}")
                
                for i, element in enumerate(clickable_elements[:15]):  # Ограничиваем количество кликов
                    try:
                        self.logger.info(f"🖱️ Клик по элементу {i+1}")
                        original_url = self.driver.current_url
                        
                        # Клик по элементу
                        self.driver.execute_script("arguments[0].click();", element)
                        try:
                            WebDriverWait(self.driver, 3).until(EC.url_changes(original_url))
                        except TimeoutException:
                            pass
                        
                        # Проверяем, изменился ли URL
                        current_url = self.driver.current_url
                        if '/org/' in current_url and current_url != original_url:
                            clean_url = current_url.split('?')[0].split('#')[0]
                            if not clean_url.endswith('/'):
                                clean_url += '/'
                            
                            if clean_url not in seen_urls:
                                seen_urls.add(clean_url)
                                business_urls.append(clean_url)
                                self.logger.info(f"   ✅ Клик {i+1}: {clean_url}")
                                
                                # Возвращаемся назад
                                self.driver.back()
                                try:
                                    WebDriverWait(self.driver, 3).until(EC.url_matches(original_url))
                                except TimeoutException:
                                    time.sleep(1)
                                
                    except Exception as e:
                        self.logger.debug(f"❌ Ошибка клика по элементу {i+1}: {e}")
                        continue
            
            self.logger.info(f"✅ Найдено {len(business_urls)} предприятий")
            
            # Автоматическое создание дашборда после парсинга
            try:
                from src.dashboard.static_dashboard import StaticDashboardGenerator
                self.logger.info("📊 Создание HTML дашборда...")
                
                dashboard_generator = StaticDashboardGenerator(session_folder=self.session_folder)
                dashboard_file = f"{self.session_folder}/dashboard_{self.session_name}.html"
                
                if dashboard_generator.generate_dashboard(dashboard_file):
                    self.logger.info(f"✅ Дашборд создан: {dashboard_file}")
                else:
                    self.logger.warning("⚠️ Не удалось создать дашборд")
                    
            except Exception as e:
                self.logger.error(f"❌ Ошибка создания дашборда: {e}")
            
            return business_urls
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения URL предприятий: {e}")
            return []
            
    def parse_businesses(self, business_urls: List[str]) -> List[Dict[str, Any]]:
        """Парсинг списка предприятий"""
        results: List[Dict[str, Any]] = []
        successful_count = 0
        failed_count = 0
        
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"🚀 НАЧАЛО ПАРСИНГА {len(business_urls)} ПРЕДПРИЯТИЙ")
        self.logger.info(f"{'='*80}")
        
        for i, business_url in enumerate(business_urls, 1):
            self.logger.info(f"\n🔄 ПРЕДПРИЯТИЕ {i}/{len(business_urls)}")
            self.logger.info(f"📄 URL: {business_url}")
            
            start_time = time.time()
            try:
                # Создание парсера для одного предприятия
                single_parser = SingleBusinessParser(session_folder=f"{self.session_folder}/businesses")
                
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
                    elapsed = time.time() - start_time
                    self.logger.info(f"✅ Предприятие {i} - УСПЕШНО за {elapsed:.1f}с")
                else:
                    failed_count += 1
                    elapsed = time.time() - start_time
                    self.logger.error(f"❌ Предприятие {i} - НЕ УДАЛОСЬ за {elapsed:.1f}с")
                    
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
            
            # Промежуточный отчет о прогрессе
            if i % 3 == 0 or i == len(business_urls):
                self.logger.info(f"📊 ПРОГРЕСС: {i}/{len(business_urls)} | ✅ Успешно: {successful_count} | ❌ Ошибок: {failed_count}")
                
        # Итоговая статистика
        self.logger.info(f"\n{'='*80}")
        self.logger.info(f"🎉 ПАРСИНГ ЗАВЕРШЕН")
        self.logger.info(f"{'='*80}")
        self.logger.info(f"📊 Статистика:")
        self.logger.info(f"   ✅ Успешно: {successful_count}")
        self.logger.info(f"   ❌ Неудачно: {failed_count}")
        self.logger.info(f"   📄 Всего: {len(business_urls)}")
        
        return results
        
    def save_summary(self, results: List[Dict[str, Any]]):
        """Сохранение сводного отчета"""
        try:
            summary_file = f"{FOLDER_STRUCTURE['base_folder']}/summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("СВОДНЫЙ ОТЧЕТ ПАРСИНГА\n")
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
            
            # Создаем генератор дашборда с указанием папки текущей сессии
            dashboard_generator = ClientDashboardGenerator(session_folder=self.session_folder)
            
            # Генерируем HTML дашборд
            dashboard_file = dashboard_generator.generate_html_dashboard()
            
            self.logger.info(f"✅ Дашборд создан: {dashboard_file}")
            self.logger.info("🌐 Откройте файл в браузере для просмотра")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка создания дашборда: {e}")
            
    def run(self) -> bool:
        """Основной метод запуска парсера"""
        try:
            self.logger.info("🚀 ЗАПУСК ОСНОВНОГО ПАРСЕРА")
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
    
    def close(self):
        """Закрытие драйвера"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("🔒 WebDriver закрыт")
            except Exception as e:
                self.logger.error(f"❌ Ошибка закрытия WebDriver: {e}")
        else:
            self.logger.warning("⚠️ WebDriver уже закрыт или не был инициализирован")


def main():
    """Точка входа"""
    print("🚀 ЗАПУСК ПАРСЕРА YANDEX MAPS")
    print("="*60)
    print(f"📄 URL поиска: {SEARCH_URL}")
    print(f"🎯 Целевое количество предприятий: {TARGET_BUSINESSES_COUNT}")
    print(f"🛍️ Целевое количество товаров: {TARGET_PRODUCTS_COUNT}")
    print("="*60)
    
    parser = MainParser()
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
