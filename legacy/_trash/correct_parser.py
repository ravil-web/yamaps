#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Правильный парсер для Яндекс Карт - использует точные селекторы из HTML
"""

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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class CorrectParser:
    def __init__(self):
        self.driver = None
        self.setup_logging()
        self.setup_folders()
        
    def setup_logging(self):
        """Настройка системы логирования"""
        os.makedirs(f"{FOLDER_STRUCTURE['base_folder']}/{FOLDER_STRUCTURE['logs_subfolder']}", exist_ok=True)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Файловый обработчик
        log_filename = f"{FOLDER_STRUCTURE['base_folder']}/{FOLDER_STRUCTURE['logs_subfolder']}/correct_parser_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_filename, encoding=LOGGING['file_encoding'])
        file_handler.setLevel(getattr(logging, LOGGING['level']))
        file_handler.setFormatter(formatter)
        
        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Настройка логгера
        self.logger = logging.getLogger('CorrectParser')
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
    
    def extract_business_urls(self):
        """Извлечение URL предприятий используя правильные селекторы"""
        business_urls = []
        try:
            self.logger.info("🔍 Поиск предприятий...")
            self.logger.info(f"📄 URL поиска: {SEARCH_URL}")
            
            self.driver.get(SEARCH_URL)
            time.sleep(DELAYS['page_load'])
            
            # Сохраняем HTML для отладки
            with open('correct_parser_debug.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            self.logger.info("💾 HTML сохранен в correct_parser_debug.html")
            
            # Ищем контейнер списка предприятий (ТОЧНЫЙ СЕЛЕКТОР)
            self.logger.info("🔍 Поиск контейнера списка предприятий...")
            
            list_container = None
            try:
                # Ищем именно search-list-view__list
                wait = WebDriverWait(self.driver, 10)
                list_container = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-list-view__list")))
                self.logger.info("✅ Найден контейнер search-list-view__list")
            except Exception as e:
                self.logger.warning(f"⚠️ Контейнер search-list-view__list не найден: {e}")
                # Попробуем альтернативные варианты
                alt_selectors = [
                    "search-list-view",
                    "search-results",
                    "business-list"
                ]
                for selector in alt_selectors:
                    try:
                        list_container = self.driver.find_element(By.CLASS_NAME, selector)
                        self.logger.info(f"✅ Найден альтернативный контейнер: {selector}")
                        break
                    except:
                        continue
            
            if not list_container:
                self.logger.error("❌ Контейнер списка не найден")
                return []
            
            # Прокрутка контейнера для загрузки всех предприятий
            self.logger.info("📜 Прокрутка контейнера для загрузки предприятий...")
            
            previous_links_count = 0
            no_change_count = 0
            
            for scroll_round in range(50):  # Максимум 50 прокруток
                # Прокручиваем контейнер списка
                try:
                    self.driver.execute_script(
                        "arguments[0].scrollTop = arguments[0].scrollTop + 800;", 
                        list_container
                    )
                    time.sleep(2)  # Даем время загрузиться
                    
                    # Также прокручиваем всю страницу
                    self.driver.execute_script("window.scrollBy(0, 500);")
                    time.sleep(1)
                    
                except Exception as e:
                    self.logger.debug(f"❌ Ошибка прокрутки: {e}")
                
                # Ищем ссылки на предприятия (ТОЧНЫЙ СЕЛЕКТОР)
                current_links = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "a.card-title-view__title-link[href*='/maps/org/']"
                )
                
                self.logger.info(f"📊 Прокрутка {scroll_round + 1}: найдено {len(current_links)} ссылок")
                
                # Проверяем, изменилось ли количество ссылок
                if len(current_links) == previous_links_count:
                    no_change_count += 1
                    self.logger.debug(f"⚠️ Количество ссылок не изменилось: {len(current_links)}")
                else:
                    no_change_count = 0
                    previous_links_count = len(current_links)
                
                # Если ссылок достаточно, останавливаемся
                if TARGET_BUSINESSES_COUNT > 0 and len(current_links) >= TARGET_BUSINESSES_COUNT:
                    self.logger.info(f"📊 Достигнуто целевое количество ссылок: {len(current_links)}")
                    break
                
                # Если количество ссылок не изменяется долго
                if no_change_count >= 8:
                    self.logger.info(f"⚠️ Количество ссылок стабильно ({len(current_links)}), попробуем дополнительную прокрутку...")
                    
                    # Принудительная прокрутка до самого конца
                    try:
                        self.driver.execute_script(
                            "arguments[0].scrollTop = arguments[0].scrollHeight;", 
                            list_container
                        )
                        time.sleep(3)
                        
                        # Ищем кнопки "Показать еще"
                        show_more_buttons = self.driver.find_elements(By.XPATH, 
                            "//button[contains(text(), 'Показать еще') or contains(text(), 'Загрузить еще')]")
                        
                        for button in show_more_buttons:
                            if button.is_displayed() and button.is_enabled():
                                self.logger.info("🔘 Нажимаем кнопку 'Показать еще'")
                                self.driver.execute_script("arguments[0].click();", button)
                                time.sleep(3)
                                break
                        
                        # Проверяем снова
                        new_links = self.driver.find_elements(
                            By.CSS_SELECTOR, 
                            "a.card-title-view__title-link[href*='/maps/org/']"
                        )
                        
                        if len(new_links) > len(current_links):
                            self.logger.info(f"✅ После дополнительной прокрутки: {len(new_links)} ссылок")
                            no_change_count = 0
                            continue
                    except:
                        pass
                    
                    # Если все равно нет изменений, завершаем
                    if no_change_count >= 12:
                        self.logger.info(f"⚠️ Завершаем поиск с {len(current_links)} найденными предприятиями")
                        break
            
            # Финальный сбор всех ссылок
            self.logger.info("🔗 Финальный сбор ссылок на предприятия...")
            
            # Используем точный селектор для ссылок
            final_links = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "a.card-title-view__title-link[href*='/maps/org/']"
            )
            
            self.logger.info(f"📊 Найдено финальных ссылок: {len(final_links)}")
            
            # Извлекаем уникальные URL
            unique_urls = set()
            
            for link in final_links:
                try:
                    href = link.get_attribute('href')
                    if href and '/maps/org/' in href:
                        # Очищаем URL от параметров
                        clean_url = href.split('?')[0].split('#')[0]
                        if not clean_url.endswith('/'):
                            clean_url += '/'
                        
                        if clean_url not in unique_urls:
                            unique_urls.add(clean_url)
                            business_urls.append(clean_url)
                            
                            # Получаем название предприятия для логирования
                            try:
                                business_name = link.text.strip() or "Без названия"
                            except:
                                business_name = "Без названия"
                            
                            self.logger.info(f"   ✅ {len(business_urls)}. {business_name}: {clean_url}")
                            
                            # Ограничиваем по целевому количеству
                            if TARGET_BUSINESSES_COUNT > 0 and len(business_urls) >= TARGET_BUSINESSES_COUNT:
                                self.logger.info(f"🎯 Достигнуто целевое количество: {TARGET_BUSINESSES_COUNT}")
                                break
                                
                except Exception as e:
                    self.logger.debug(f"❌ Ошибка обработки ссылки: {e}")
                    continue
            
            self.logger.info(f"✅ Извлечено уникальных URL предприятий: {len(business_urls)}")
            
            if len(business_urls) == 0:
                self.logger.error("❌ Не найдено ни одного URL предприятия")
                # Дополнительная диагностика
                self.logger.info("🔍 Дополнительная диагностика...")
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                org_links = [link for link in all_links if '/org/' in (link.get_attribute('href') or '')]
                self.logger.info(f"📊 Всего ссылок на странице: {len(all_links)}")
                self.logger.info(f"📊 Ссылок с '/org/': {len(org_links)}")
                
                if org_links:
                    self.logger.info("🔍 Первые 5 ссылок с '/org/':")
                    for i, link in enumerate(org_links[:5]):
                        self.logger.info(f"   {i+1}. {link.get_attribute('href')}")
            
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
            summary_file = f"{FOLDER_STRUCTURE['base_folder']}/correct_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("СВОДНЫЙ ОТЧЕТ ПРАВИЛЬНОГО ПАРСЕРА\n")
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
            
            # Создаем дашборд
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
            self.logger.info("🚀 ЗАПУСК ПРАВИЛЬНОГО ПАРСЕРА")
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
            
            # Сохранение сводного отчета
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
    print("🚀 ЗАПУСК ПРАВИЛЬНОГО ПАРСЕРА YANDEX MAPS")
    print("="*60)
    print(f"📄 URL поиска: {SEARCH_URL}")
    print(f"🎯 Целевое количество предприятий: {TARGET_BUSINESSES_COUNT}")
    print(f"🛍️ Целевое количество товаров: {TARGET_PRODUCTS_COUNT}")
    print("="*60)
    
    parser = CorrectParser()
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
