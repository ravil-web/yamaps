import time
import json
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains

class SellerParser:
    def __init__(self, headless=False):
        """
        Инициализация парсера для товаров продавца
        :param headless: True для работы без отображения браузера
        """
        self.options = Options()
        
        # Настройки для имитации реального браузера
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Дополнительные настройки для обхода блокировок
        self.options.add_argument('--disable-web-security')
        self.options.add_argument('--allow-running-insecure-content')
        self.options.add_argument('--disable-features=VizDisplayCompositor')
        self.options.add_argument('--disable-extensions')
        
        if headless:
            self.options.add_argument('--headless')
        
        # Дополнительные настройки для стабильности
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--window-size=1920,1080')
        
        self.driver = None
        
    def start_driver(self):
        """Запуск драйвера"""
        try:
            self.driver = webdriver.Chrome(options=self.options)
            
            # Убираем признаки автоматизации
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver.maximize_window()
            print("Браузер успешно запущен")
        except Exception as e:
            print(f"Ошибка при запуске драйвера: {e}")
            raise
    
    def check_for_blocking(self):
        """Проверка на блокировку или капчу"""
        try:
            # Проверяем наличие капчи
            captcha = self.driver.find_elements(By.CSS_SELECTOR, '[class*="captcha"], [class*="recaptcha"]')
            if captcha:
                print("Обнаружена капча! Ожидание 30 секунд...")
                time.sleep(30)
                return True
            
            # Проверяем блокировку
            blocking = self.driver.find_elements(By.CSS_SELECTOR, '[class*="block"], [class*="error"]')
            if blocking:
                print("Обнаружена блокировка!")
                return True
                
            return False
        except:
            return False
    
    def _debug_page_structure(self):
        """Отладочная функция для анализа структуры страницы продавца"""
        print("\n=== АНАЛИЗ СТРУКТУРЫ СТРАНИЦЫ ПРОДАВЦА ===")
        
        # Проверяем наличие различных элементов
        selectors_to_check = [
            '[data-widget="tileGridDesktop"]',
            'div[data-index]',
            '[class*="tile-root"]',
            '[class*="i6p_24"]',
            'a[href*="/product/"]',
            'span[class*="tsBody500Medium"]',
            'span[class*="tsHeadline500Medium"]',
            '[class*="c35_3_1-a1"]',
            '[class*="seller"]',
            '[class*="vendor"]'
        ]
        
        for selector in selectors_to_check:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"{selector}: найдено {len(elements)} элементов")
            except:
                print(f"{selector}: ошибка поиска")
        
        # Проверяем все ссылки на товары
        try:
            product_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/product/"]')
            print(f"Ссылок на товары: {len(product_links)}")
            
            if product_links:
                print("Примеры ссылок:")
                for i, link in enumerate(product_links[:3]):
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    print(f"  {i+1}. {href} - '{text}'")
        except Exception as e:
            print(f"Ошибка при поиске ссылок: {e}")
        
        # Проверяем карточки товаров
        try:
            cards = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-index]')
            print(f"Карточек товаров: {len(cards)}")
            
            if cards:
                print("Примеры карточек:")
                for i, card in enumerate(cards[:2]):
                    try:
                        name = card.find_element(By.CSS_SELECTOR, 'span[class*="tsBody500Medium"]').text.strip()
                        print(f"  {i+1}. {name}")
                    except:
                        print(f"  {i+1}. Название не найдено")
        except Exception as e:
            print(f"Ошибка при поиске карточек: {e}")
        
        print("=== КОНЕЦ АНАЛИЗА ===\n")

    def _debug_product_detail(self):
        """
        Отладочная функция для проверки структуры страницы товара
        """
        try:
            print("\n=== ОТЛАДКА СТРУКТУРЫ СТРАНИЦЫ ТОВАРА ===")
            
            # Проверяем наличие названия товара
            names = self.driver.find_elements(By.CSS_SELECTOR, 'h1.tsHeadline550Medium')
            print(f"Найдено названий товара (h1.tsHeadline550Medium): {len(names)}")
            
            names_alt = self.driver.find_elements(By.CSS_SELECTOR, 'h1.lm1_27')
            print(f"Найдено названий товара (h1.lm1_27): {len(names_alt)}")
            
            if names:
                print("Примеры названий:")
                for i, name in enumerate(names[:2]):
                    text = name.text.strip()
                    if text:
                        print(f"  {i+1}. {text[:50]}...")
            
            # Проверяем наличие цены
            prices = self.driver.find_elements(By.CSS_SELECTOR, 'span.zk5_27.z3k_27')
            print(f"Найдено цен (span.zk5_27.z3k_27): {len(prices)}")
            
            prices_alt = self.driver.find_elements(By.CSS_SELECTOR, 'span[class*="zk5"]')
            print(f"Найдено цен (span[class*=\"zk5\"]): {len(prices_alt)}")
            
            if prices:
                print("Примеры цен:")
                for i, price in enumerate(prices[:2]):
                    text = price.text.strip()
                    if text:
                        print(f"  {i+1}. {text}")
            
            # Проверяем наличие рейтинга
            ratings = self.driver.find_elements(By.CSS_SELECTOR, 'div.ga5_3_1-a2')
            print(f"Найдено рейтингов (div.ga5_3_1-a2): {len(ratings)}")
            
            if ratings:
                print("Примеры рейтингов:")
                for i, rating in enumerate(ratings[:2]):
                    text = rating.text.strip()
                    if text:
                        print(f"  {i+1}. {text}")
            
            # Проверяем наличие описания
            descriptions = self.driver.find_elements(By.CSS_SELECTOR, 'div.k6k_27')
            print(f"Найдено описаний (div.k6k_27): {len(descriptions)}")
            
            if descriptions:
                print("Примеры описаний:")
                for i, desc in enumerate(descriptions[:2]):
                    text = desc.text.strip()
                    if text:
                        print(f"  {i+1}. {text[:100]}...")
            
            # Проверяем наличие характеристик
            specs = self.driver.find_elements(By.CSS_SELECTOR, 'div.rl8_27')
            print(f"Найдено характеристик (div.rl8_27): {len(specs)}")
            
            if specs:
                print("Примеры характеристик:")
                for i, spec in enumerate(specs[:2]):
                    text = spec.text.strip()
                    if text:
                        print(f"  {i+1}. {text[:100]}...")
            
            print("=== КОНЕЦ ОТЛАДКИ СТРАНИЦЫ ТОВАРА ===\n")
            
        except Exception as e:
            print(f"Ошибка при отладке структуры страницы товара: {e}")

    def parse_seller_products(self, seller_url, max_products=200, max_pages=10):
        """
        Парсинг товаров продавца по URL
        :param seller_url: URL страницы продавца
        :param max_products: максимальное количество товаров для парсинга
        :param max_pages: максимальное количество страниц для парсинга
        :return: список словарей с информацией о товарах
        """
        if not self.driver:
            self.start_driver()
        
        products = []
        current_page = 1
        
        try:
            print(f"Переход на страницу продавца: {seller_url}")
            self.driver.get(seller_url)
            
            # Случайная задержка
            time.sleep(random.uniform(3, 6))
            
            while len(products) < max_products and current_page <= max_pages:
                print(f"Обработка страницы {current_page} (найдено товаров: {len(products)})")
                
                # Проверка на блокировку
                if self.check_for_blocking():
                    print("Пропуск страницы из-за блокировки")
                    break
                
                # Прокручиваем страницу для загрузки товаров
                self._scroll_page()
                
                # Отладочная информация (только для первых страниц)
                if current_page <= 3:
                    self._debug_page_structure()
                
                # Ждем появления товаров
                wait = WebDriverWait(self.driver, 20)
                try:
                    # Пробуем найти товары разными способами
                    product_cards = self._find_product_cards_direct()
                    
                    if not product_cards:
                        print("Пробуем альтернативный способ поиска...")
                        product_cards = self._find_product_cards_alternative()
                    
                    if not product_cards:
                        print("Пробуем JavaScript поиск...")
                        product_cards = self._find_product_cards_js()
                    
                    if not product_cards:
                        print("Пробуем XPath поиск...")
                        product_cards = self._find_product_cards_xpath()
                    
                    if not product_cards:
                        print("Пробуем универсальный поиск...")
                        product_cards = self._find_product_cards_universal()
                    
                    print(f"Найдено {len(product_cards)} товаров на странице")
                    
                    for i, card in enumerate(product_cards):
                        if len(products) >= max_products:
                            break
                            
                        try:
                            product_data = self._extract_product_data(card)
                            if product_data and product_data not in products:
                                products.append(product_data)
                                if len(products) % 10 == 0:  # Выводим каждые 10 товаров
                                    print(f"Обработан товар {len(products)}: {product_data['name'][:50]}...")
                        except Exception as e:
                            print(f"Ошибка при обработке товара: {e}")
                            continue
                    
                    # Переход на следующую страницу
                    if len(products) < max_products and current_page < max_pages:
                        if not self._go_to_next_page():
                            print("Следующая страница не найдена")
                            break
                        current_page += 1
                        time.sleep(random.uniform(3, 6))
                    else:
                        break
                        
                except TimeoutException:
                    print("Превышено время ожидания загрузки страницы")
                    break
                    
        except Exception as e:
            print(f"Ошибка при парсинге: {e}")
        
        return products
    
    def parse_seller_products_with_details(self, seller_url, max_products=200, max_pages=10):
        """
        Парсинг товаров продавца с переходом в карточки для получения детальной информации
        :param seller_url: URL страницы продавца
        :param max_products: максимальное количество товаров для парсинга
        :param max_pages: максимальное количество страниц для парсинга
        :return: список словарей с детальной информацией о товарах
        """
        if not self.driver:
            self.start_driver()
        
        all_product_links = []
        current_page = 1
        
        try:
            print(f"Переход на страницу продавца: {seller_url}")
            self.driver.get(seller_url)
            
            # Случайная задержка
            time.sleep(random.uniform(3, 6))
            
            while len(all_product_links) < max_products and current_page <= max_pages:
                print(f"Обработка страницы {current_page} (собрано ссылок: {len(all_product_links)})")
                
                # Проверка на блокировку
                if self.check_for_blocking():
                    print("Пропуск страницы из-за блокировки")
                    break
                
                # Прокручиваем страницу для загрузки товаров
                self._scroll_page()
                
                # Отладочная информация (только для первых страниц)
                if current_page <= 3:
                    self._debug_page_structure()
                
                # Собираем ссылки на товары
                try:
                    product_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/product/"]')
                    
                    for link in product_links:
                        if len(all_product_links) >= max_products:
                            break
                        
                        href = link.get_attribute('href')
                        if href and href not in all_product_links:
                            all_product_links.append(href)
                    
                    print(f"Собрано {len(all_product_links)} ссылок на товары")
                    
                    # Переход на следующую страницу
                    if len(all_product_links) < max_products and current_page < max_pages:
                        if not self._go_to_next_page():
                            print("Следующая страница не найдена")
                            break
                        current_page += 1
                        time.sleep(random.uniform(3, 6))
                    else:
                        break
                        
                except Exception as e:
                    print(f"Ошибка при сборе ссылок: {e}")
                    break
                    
        except Exception as e:
            print(f"Ошибка при парсинге: {e}")
        
        # Парсим детальную информацию по каждой ссылке
        print(f"\nНачинаем парсинг детальной информации для {len(all_product_links)} товаров...")
        detailed_products = self.parse_product_details(all_product_links, max_products)
        
        return detailed_products
    
    def parse_product_details(self, product_links, max_products=200):
        """
        Парсинг детальной информации о товарах через переход в карточки
        :param product_links: список ссылок на товары
        :param max_products: максимальное количество товаров для парсинга
        :return: список словарей с детальной информацией о товарах
        """
        detailed_products = []
        
        for i, link in enumerate(product_links[:max_products]):
            try:
                print(f"Обработка товара {i+1}/{min(len(product_links), max_products)}")
                
                # Переходим на страницу товара
                self.driver.get(link)
                time.sleep(random.uniform(2, 4))
                
                # Проверка на блокировку
                if self.check_for_blocking():
                    print("Пропуск товара из-за блокировки")
                    continue
                
                # Отладочная информация для страницы товара (только для первых товаров)
                if i < 5:
                    self._debug_product_detail()
                
                # Извлекаем детальную информацию
                product_detail = self._extract_product_detail()
                if product_detail:
                    detailed_products.append(product_detail)
                    if len(detailed_products) % 10 == 0:  # Выводим каждые 10 товаров
                        print(f"Обработан товар: {product_detail['name'][:50]}...")
                
                # Случайная задержка между товарами
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f"Ошибка при обработке товара {i+1}: {e}")
                continue
        
        return detailed_products
    
    def _find_product_cards_alternative(self):
        """Альтернативный поиск карточек товаров"""
        try:
            # Ищем все ссылки на товары
            product_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="/product/"]')
            
            # Находим родительские элементы ссылок
            cards = []
            for link in product_links:
                try:
                    # Поднимаемся на несколько уровней вверх для поиска карточки
                    card = link
                    for _ in range(5):
                        card = card.find_element(By.XPATH, '..')
                        if card:
                            cards.append(card)
                            break
                except:
                    continue
            
            return list(set(cards))  # Убираем дубликаты
        except:
            return []
    
    def _find_product_cards_js(self):
        """Поиск карточек товаров через JavaScript"""
        try:
            # JavaScript для поиска всех элементов с ссылками на товары
            js_script = """
            var cards = [];
            var links = document.querySelectorAll('a[href*="/product/"]');
            
            for (var i = 0; i < links.length; i++) {
                var link = links[i];
                var parent = link.parentElement;
                
                // Ищем карточку товара (обычно это div с определенной структурой)
                for (var j = 0; j < 5; j++) {
                    if (parent && parent.tagName === 'DIV') {
                        cards.push(parent);
                        break;
                    }
                    parent = parent ? parent.parentElement : null;
                }
            }
            
            return cards;
            """
            
            cards = self.driver.execute_script(js_script)
            return cards
        except Exception as e:
            print(f"Ошибка JavaScript поиска: {e}")
            return []
    
    def _find_product_cards_universal(self):
        """Универсальный поиск карточек товаров через все элементы"""
        try:
            # Ищем все div элементы на странице
            all_divs = self.driver.find_elements(By.TAG_NAME, 'div')
            cards = []
            
            for div in all_divs:
                try:
                    # Проверяем, содержит ли div ссылку на товар
                    product_link = div.find_element(By.CSS_SELECTOR, 'a[href*="/product/"]')
                    if product_link:
                        # Проверяем, что это не реклама или баннер
                        div_text = div.text.strip()
                        if len(div_text) > 10 and 'реклама' not in div_text.lower():
                            cards.append(div)
                except:
                    continue
            
            return list(set(cards))  # Убираем дубликаты
        except Exception as e:
            print(f"Ошибка универсального поиска: {e}")
            return []
    
    def _find_product_cards_xpath(self):
        """Поиск карточек товаров через XPath"""
        try:
            # XPath селекторы для поиска карточек товаров
            xpath_selectors = [
                "//div[contains(@class, 'tsBody')]",
                "//div[contains(@style, 'grid-column')]",
                "//div[contains(@data-widget, 'card')]",
                "//div[contains(@class, 'product')]",
                "//div[contains(@class, 'item')]",
                "//a[contains(@href, '/product/')]/..",
                "//a[contains(@href, '/product/')]/../.."
            ]
            
            for xpath in xpath_selectors:
                try:
                    cards = self.driver.find_elements(By.XPATH, xpath)
                    if cards:
                        print(f"Найдены карточки с XPath: {xpath}")
                        return cards
                except:
                    continue
            
            return []
        except Exception as e:
            print(f"Ошибка XPath поиска: {e}")
            return []
    
    def _find_product_cards_direct(self):
        """Прямой поиск карточек товаров"""
        selectors = [
            '[data-widget="tileGridDesktop"] div[data-index]',
            'div[data-index]',
            '[class*="tile-root"]',
            '[class*="i6p_24"]'
        ]
        
        for selector in selectors:
            try:
                cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if cards:
                    print(f"Найдены карточки с селектором: {selector}")
                    return cards
            except:
                continue
        
        return []
    
    def _go_to_next_page(self):
        """Переход на следующую страницу"""
        try:
            # Ищем кнопку "Следующая страница"
            next_selectors = [
                '[data-widget="paginator"] a[aria-label*="Следующая"]',
                '[data-widget="paginator"] a[aria-label*="Next"]',
                '[class*="pagination"] a[class*="next"]',
                'a[href*="page="]',
                'button[aria-label*="Следующая"]',
                'button[aria-label*="Next"]'
            ]
            
            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button.is_enabled():
                        next_button.click()
                        time.sleep(random.uniform(2, 4))
                        return True
                except:
                    continue
            
            return False
        except:
            return False
    
    def _scroll_page(self):
        """Прокрутка страницы для загрузки динамического контента"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for i in range(8):  # Увеличиваем количество прокруток
            # Прокрутка вниз
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 4))
            
            # Проверка, изменилась ли высота страницы
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
    
    def _extract_product_data(self, card):
        """
        Извлечение данных о товаре из карточки с актуальными селекторами
        :param card: элемент карточки товара
        :return: словарь с данными о товаре
        """
        product = {}
        
        try:
            # Название товара - актуальные селекторы
            name_selectors = [
                'span[class*="tsBody500Medium"]',
                '[class*="bq02_4_0-a"] span',
                'a[href*="/product/"] span[class*="tsBody"]',
                'span[class*="tsBody"]'
            ]
            
            product['name'] = self._extract_text(card, name_selectors, 'Название не найдено')
            
            # Если название не найдено, пробуем извлечь из ссылки
            if product['name'] == 'Название не найдено':
                try:
                    link_element = card.find_element(By.CSS_SELECTOR, 'a[href*="/product/"]')
                    product['name'] = link_element.get_attribute('title') or link_element.text.strip() or 'Название не найдено'
                except:
                    pass
            
            # Цена - актуальные селекторы
            price_selectors = [
                'span[class*="tsHeadline500Medium"]',
                'span[class*="tsHeadline"]',
                '[class*="c35_3_1-a1"][class*="tsHeadline"]',
                'span[class*="c35_3_1-a1"]'
            ]
            
            price_text = self._extract_text(card, price_selectors, 'Цена не указана')
            if price_text != 'Цена не указана':
                # Убираем символы и пробелы, оставляем только цифры
                product['price'] = ''.join(filter(str.isdigit, price_text))
            else:
                product['price'] = price_text
            
            # Рейтинг - актуальные селекторы
            rating_selectors = [
                'span[style*="color: rgb(255, 165, 0)"]',
                'span[style*="color: rgba(255, 165, 0, 1)"]',
                '[class*="p6b2_4_0-a4"] span[style*="color"]',
                'span[class*="p6b2_4_0-a4"]'
            ]
            product['rating'] = self._extract_text(card, rating_selectors, 'Нет рейтинга')
            
            # Количество отзывов - актуальные селекторы
            reviews_selectors = [
                'span[style*="color: rgba(0, 26, 52, 0.6)"]',
                'span[style*="color: rgb(0, 26, 52, 0.6)"]',
                '[class*="p6b2_4_0-a4"] span[style*="color"]',
                'span[class*="p6b2_4_0-a4"]'
            ]
            product['reviews'] = self._extract_text(card, reviews_selectors, '0 отзывов')
            
            # Ссылка на товар
            try:
                link_element = card.find_element(By.CSS_SELECTOR, 'a[href*="/product/"]')
                href = link_element.get_attribute('href')
                if href.startswith('/'):
                    product['link'] = 'https://www.ozon.ru' + href
                else:
                    product['link'] = href
            except NoSuchElementException:
                product['link'] = 'Ссылка не найдена'
            
            # Информация о доставке - актуальные селекторы
            delivery_selectors = [
                'button[class*="b25_3_1-a0"] div[class*="tsBodyControl500Medium"]',
                '[class*="b25_3_1-a8"]',
                'div[class*="tsBodyControl500Medium"]'
            ]
            product['delivery'] = self._extract_text(card, delivery_selectors, 'Информация о доставке отсутствует')
            
            return product
            
        except Exception as e:
            print(f"Ошибка при извлечении данных: {e}")
            return None
    
    def _extract_text(self, element, selectors, default_text):
        """Извлечение текста с использованием нескольких селекторов"""
        for selector in selectors:
            try:
                found_element = element.find_element(By.CSS_SELECTOR, selector)
                text = found_element.text.strip()
                if text:
                    return text
            except NoSuchElementException:
                continue
        return default_text
    
    def _extract_product_detail(self):
        """
        Извлечение детальной информации о товаре со страницы карточки
        :return: словарь с детальной информацией о товаре
        """
        product = {}
        
        try:
            # Название товара - h1 с классом tsHeadline550Medium
            name_selectors = [
                'h1.tsHeadline550Medium',
                'h1.lm1_27',
                'h1[class*="tsHeadline"]',
                'h1[class*="lm1"]',
                'h1',
                '[class*="product-title"] h1'
            ]
            product['name'] = self._extract_text(self.driver, name_selectors, 'Название не найдено')
            
            # Цена - из блока с классами zk5_27 z3k_27
            price_selectors = [
                'span.zk5_27.z3k_27',
                'span[class*="zk5"]',
                'span[class*="z3k"]',
                'span[class*="price"]',
                '[class*="price"] span[class*="tsHeadline"]',
                'span[class*="tsHeadline"][class*="price"]',
                'span[class*="ll0"]'
            ]
            price_text = self._extract_text(self.driver, price_selectors, 'Цена не указана')
            if price_text != 'Цена не указана':
                # Извлекаем только цифры из цены
                price_digits = ''.join(filter(str.isdigit, price_text))
                product['price'] = price_digits if price_digits else price_text
            else:
                product['price'] = price_text
            
            # Рейтинг - из блока с классом ga5_3_1-a2
            rating_selectors = [
                'div.ga5_3_1-a2',
                'div[class*="ga5_3_1-a2"]',
                'div[class*="ga5_3_1"]',
                '[class*="rating"] span',
                '[class*="stars"] span',
                'span[class*="rating"]',
                'a[class*="ga5_3_1-a"] div[class*="ga5_3_1-a2"]'
            ]
            rating_text = self._extract_text(self.driver, rating_selectors, 'Нет рейтинга')
            if rating_text != 'Нет рейтинга':
                # Извлекаем рейтинг из текста вида "4.8 • 2 691 отзыв"
                import re
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    product['rating'] = rating_match.group(1)
                else:
                    product['rating'] = rating_text
            else:
                product['rating'] = rating_text
            
            # Количество отзывов - из того же блока что и рейтинг
            reviews_selectors = [
                'div.ga5_3_1-a2',
                'div[class*="ga5_3_1-a2"]',
                'div[class*="ga5_3_1"]',
                '[class*="reviews"] span',
                '[class*="feedback"] span',
                'span[class*="reviews"]',
                'a[class*="ga5_3_1-a"] div[class*="ga5_3_1-a2"]'
            ]
            reviews_text = self._extract_text(self.driver, reviews_selectors, '0 отзывов')
            if reviews_text != '0 отзывов':
                # Извлекаем количество отзывов из текста вида "4.8 • 2 691 отзыв"
                import re
                reviews_match = re.search(r'(\d+(?:\s+\d+)*)\s+отзыв', reviews_text)
                if reviews_match:
                    product['reviews'] = reviews_match.group(1)
                else:
                    product['reviews'] = reviews_text
            else:
                product['reviews'] = reviews_text
            
            # Описание товара - из блока с классом k6k_27
            description_selectors = [
                'div.k6k_27',
                'div[class*="k6k_27"]',
                'div[class*="k6k"]',
                '[class*="description"]',
                '[class*="product-description"]',
                'div[class*="tsBody"]',
                'div[class*="kk6"]'
            ]
            product['description'] = self._extract_text(self.driver, description_selectors, 'Описание отсутствует')
            
            # Характеристики товара - из блока с классом rl8_27
            specs_selectors = [
                'div.rl8_27',
                'div[class*="rl8_27"]',
                'div[class*="rl8"]',
                '[class*="specifications"]',
                '[class*="characteristics"]',
                '[class*="features"]',
                'div[class*="rl4"]'
            ]
            specs_text = self._extract_text(self.driver, specs_selectors, 'Характеристики отсутствуют')
            if specs_text != 'Характеристики отсутствуют':
                # Очищаем текст характеристик
                specs_clean = specs_text.replace('\n', ' ').strip()
                product['specifications'] = specs_clean
            else:
                product['specifications'] = specs_text
            
            # Доставка - из блока с информацией о доставке
            delivery_selectors = [
                'span[class*="q6b2_4_0-a"]',
                'span[class*="q6b2"]',
                '[class*="delivery"]',
                '[class*="shipping"]',
                'span[class*="delivery"]',
                'div[class*="z7j"]'
            ]
            delivery_text = self._extract_text(self.driver, delivery_selectors, 'Информация о доставке отсутствует')
            if delivery_text != 'Информация о доставке отсутствует':
                # Ищем информацию о доставке в тексте
                if 'Курьером' in delivery_text or 'Пункты выдачи' in delivery_text or 'Почтой' in delivery_text:
                    product['delivery'] = delivery_text
                else:
                    product['delivery'] = 'Информация о доставке отсутствует'
            else:
                product['delivery'] = delivery_text
            
            # Продавец - из блока с классом rl6_27
            seller_selectors = [
                'a.rl6_27',
                'a[class*="rl6_27"]',
                'a[class*="rl6"]',
                '[class*="seller"]',
                '[class*="vendor"]',
                'span[class*="seller"]',
                'div[class*="lr7"]'
            ]
            product['seller'] = self._extract_text(self.driver, seller_selectors, 'Продавец не указан')
            
            # Артикул/ID - из URL или специального блока
            sku_selectors = [
                '[class*="sku"]',
                '[class*="article"]',
                '[class*="product-id"]',
                'span[class*="sku"]'
            ]
            sku_text = self._extract_text(self.driver, sku_selectors, 'Артикул не указан')
            if sku_text == 'Артикул не указан':
                # Пытаемся извлечь ID из URL
                url = self.driver.current_url
                import re
                sku_match = re.search(r'/product/.*?-(\d+)/', url)
                if sku_match:
                    product['sku'] = sku_match.group(1)
                else:
                    product['sku'] = sku_text
            else:
                product['sku'] = sku_text
            
            # URL страницы
            product['url'] = self.driver.current_url
            
            # Дополнительная обработка данных
            try:
                # Очистка названия от лишних пробелов
                if product['name'] != 'Название не найдено':
                    product['name'] = product['name'].strip()
                
                # Очистка цены от символов валюты
                if product['price'] != 'Цена не указана' and isinstance(product['price'], str):
                    # Убираем символы валюты и пробелы
                    import re
                    price_clean = re.sub(r'[^\d]', '', product['price'])
                    if price_clean:
                        product['price'] = price_clean
                
                # Очистка рейтинга
                if product['rating'] != 'Нет рейтинга' and isinstance(product['rating'], str):
                    # Убираем лишние символы
                    rating_clean = re.sub(r'[^\d.]', '', product['rating'])
                    if rating_clean:
                        product['rating'] = rating_clean
                
                # Очистка количества отзывов
                if product['reviews'] != '0 отзывов' and isinstance(product['reviews'], str):
                    # Убираем лишние символы
                    reviews_clean = re.sub(r'[^\d]', '', product['reviews'])
                    if reviews_clean:
                        product['reviews'] = reviews_clean
                
            except Exception as e:
                print(f"Ошибка при очистке данных: {e}")
            
            return product
            
        except Exception as e:
            print(f"Ошибка при извлечении детальной информации: {e}")
            return None
    
    def save_to_json(self, products, filename='seller_products.json'):
        """
        Сохранение результатов в JSON файл
        :param products: список товаров
        :param filename: имя файла
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"Результаты сохранены в файл {filename}")
    
    def close(self):
        """Закрытие браузера"""
        if self.driver:
            self.driver.quit()
            print("Браузер закрыт")

def main():
    # URL для парсинга товаров продавца
    seller_url = "https://www.ozon.ru/seller/izdatelstvo-azbuka-449426/products/?miniapp=seller_449426"
    
    # Создаем парсер
    parser = SellerParser(headless=False)  # headless=True для работы без окна браузера
    
    try:
        print("=== ПАРСИНГ ТОВАРОВ ПРОДАВЦА С ДЕТАЛЬНОЙ ИНФОРМАЦИЕЙ ===")
        
        # Парсим товары продавца с переходом в карточки
        detailed_products = parser.parse_seller_products_with_details(seller_url, max_products=200, max_pages=10)
        
        # Выводим результаты
        print(f"\nНайдено {len(detailed_products)} товаров продавца с детальной информацией:")
        for i, product in enumerate(detailed_products, 1):
            print(f"\n{i}. {product['name']}")
            print(f"   Цена: {product['price']} ₽")
            print(f"   Рейтинг: {product['rating']}")
            print(f"   Отзывы: {product['reviews']}")
            print(f"   Продавец: {product['seller']}")
            print(f"   Артикул: {product['sku']}")
            print(f"   Доставка: {product['delivery']}")
            print(f"   Описание: {product['description'][:100]}...")
            print(f"   Характеристики: {product['specifications'][:100]}...")
            print(f"   URL: {product['url']}")
        
        # Сохраняем в файл
        parser.save_to_json(detailed_products, 'seller_detailed_products.json')
        
        print("\n=== ОБЫЧНЫЙ ПАРСИНГ ТОВАРОВ ПРОДАВЦА ===")
        
        # Обычный парсинг для сравнения
        products = parser.parse_seller_products(seller_url, max_products=200, max_pages=10)
        
        # Выводим результаты
        print(f"\nНайдено {len(products)} товаров продавца (обычный парсинг):")
        for i, product in enumerate(products, 1):
            print(f"\n{i}. {product['name']}")
            print(f"   Цена: {product['price']} ₽")
            print(f"   Рейтинг: {product['rating']}")
            print(f"   Отзывы: {product['reviews']}")
            print(f"   Доставка: {product['delivery']}")
            print(f"   Ссылка: {product['link']}")
        
        # Сохраняем в файл
        parser.save_to_json(products, 'seller_products.json')
        
    finally:
        # Закрываем браузер
        input("\nНажмите Enter для закрытия браузера...")
        parser.close()

if __name__ == "__main__":
    main() 