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


class MainParser:
    def __init__(self):
        self.driver = None
        self.setup_logging()
        self.setup_folders()
        
    def setup_logging(self):
        """Настройка системы логирования"""
        os.makedirs(f"{FOLDER_STRUCTURE['base_folder']}/{FOLDER_STRUCTURE['logs_subfolder']}", exist_ok=True)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Файловый обработчик
        log_filename = f"{FOLDER_STRUCTURE['base_folder']}/{FOLDER_STRUCTURE['logs_subfolder']}/main_parser_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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
            self.driver.implicitly_wait(5)
            self.logger.info("✅ WebDriver инициализирован успешно")
            return True
        except Exception as e:
            self.logger.error(f"❌ Ошибка инициализации WebDriver: {e}")
            return False

    def extract_business_urls(self):
        """Извлечение URL предприятий - РАБОЧИЙ МЕТОД из simple_working_parser"""
        business_urls = []
        try:
            self.logger.info("🔍 Поиск предприятий...")
            self.logger.info(f"📄 URL поиска: {SEARCH_URL}")
            
            self.driver.get(SEARCH_URL)
            time.sleep(DELAYS['page_load'])
            
            # РАБОЧИЙ МЕТОД: Массивная прокрутка для загрузки всех предприятий
            self.logger.info("📜 Выполняем массивную прокрутку для загрузки предприятий...")
            for scroll_round in range(20):  # 20 раундов прокрутки
                self.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(1.5)
                
                # Дополнительная прокрутка в разные стороны для активации загрузки
                self.driver.execute_script("window.scrollBy(500, 0);")
                time.sleep(0.5)
                self.driver.execute_script("window.scrollBy(-500, 0);")
                time.sleep(0.5)
                
                if scroll_round % 5 == 0:
                    self.logger.info(f"📜 Выполнено {scroll_round + 1} раундов прокрутки")
            
            # РАБОЧИЙ МЕТОД: Поиск ВСЕХ ссылок с /org/ (проверенный способ)
            self.logger.info("🔍 Поиск всех ссылок на организации...")
            all_org_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/org/')]")
            self.logger.info(f"📊 Найдено всех ссылок с /org/: {len(all_org_links)}")
            
            # Фильтруем и собираем уникальные URL
            seen_urls = set()
            for link in all_org_links:
                try:
                    href = link.get_attribute('href')
                    if href and '/org/' in href:
                        # Исключаем ссылки на отзывы, галереи и фото
                        if any(exclude in href for exclude in ['/reviews/', '/gallery/', '/photos/']):
                            continue
                        
                        # Очищаем URL
                        clean_url = href.split('?')[0].split('#')[0]
                        if not clean_url.endswith('/'):
                            clean_url += '/'
                        
                        if clean_url not in seen_urls:
                            seen_urls.add(clean_url)
                            business_urls.append(clean_url)
                            
                            # Пробуем получить название для лога
                            try:
                                name = link.text.strip() or "Без названия"
                                if len(name) > 50:  # Обрезаем длинные названия
                                    name = name[:50] + "..."
                            except:
                                name = "Без названия"
                            
                            self.logger.info(f"   ✅ {len(business_urls)}. {name}")
                            
                            # Останавливаемся при достижении цели
                            if TARGET_BUSINESSES_COUNT > 0 and len(business_urls) >= TARGET_BUSINESSES_COUNT:
                                self.logger.info(f"🎯 Достигнуто целевое количество: {TARGET_BUSINESSES_COUNT}")
                                break
                                
                except Exception as e:
                    self.logger.debug(f"❌ Ошибка обработки ссылки: {e}")
                    continue
            
            # Если найдено мало ссылок, пробуем клики по элементам (дополнительный метод)
            if len(business_urls) < 10:
                self.logger.info("🖱️ Мало ссылок, пробуем клики по элементам...")
                clickable_elements = self.driver.find_elements(By.XPATH, "//*[contains(@data-id, '') or contains(@class, 'placemark') or contains(@class, 'marker')]")
                self.logger.info(f"📊 Найдено кликабельных элементов: {len(clickable_elements)}")
                
                for i, element in enumerate(clickable_elements[:15]):  # Ограничиваем количество кликов
                    try:
                        self.logger.info(f"🖱️ Клик по элементу {i+1}")
                        original_url = self.driver.current_url
                        
                        # Клик по элементу
                        self.driver.execute_script("arguments[0].click();", element)
                        time.sleep(3)
                        
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
                                time.sleep(2)
                                
                    except Exception as e:
                        self.logger.debug(f"❌ Ошибка клика по элементу {i+1}: {e}")
                        continue
            
            self.logger.info(f"✅ Найдено {len(business_urls)} предприятий")
            return business_urls
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка извлечения URL предприятий: {e}")
            return []
            
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
            
            # Создаем генератор дашборда
            dashboard_generator = ClientDashboardGenerator()
            
            # Генерируем HTML дашборд
            dashboard_file = dashboard_generator.generate_html_dashboard()
            
            self.logger.info(f"✅ Дашборд создан: {dashboard_file}")
            self.logger.info("🌐 Откройте файл в браузере для просмотра")
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка создания дашборда: {e}")
            
    def run(self):
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
