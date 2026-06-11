#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Умная диагностика и исправление селекторов для медленного парсинга
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

class SmartSelectorsFix:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Инициализация WebDriver"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(3)
    
    def analyze_and_fix_selectors(self, url):
        """Анализ и создание оптимальных селекторов"""
        print(f"🔍 Анализируем структуру товаров: {url}")
        
        self.driver.get(url)
        time.sleep(5)
        
        # Находим элементы товаров
        print("📊 Поиск элементов товаров...")
        product_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'business-full-items-grouped-view__item')]")
        
        if not product_elements:
            print("❌ Элементы товаров не найдены")
            return
        
        print(f"✅ Найдено {len(product_elements)} товаров")
        
        # Анализируем первые 3 товара для понимания структуры
        optimal_selectors = {
            'title': [],
            'price': []
        }
        
        for i, elem in enumerate(product_elements[:3]):
            print(f"\n🔍 Анализ товара {i+1}:")
            
            # Получаем HTML элемента
            elem_html = elem.get_attribute('outerHTML')
            print(f"   HTML длина: {len(elem_html)} символов")
            
            # Ищем все элементы внутри с текстом
            title_candidates = []
            price_candidates = []
            
            # Все элементы с текстом
            all_text_elements = elem.find_elements(By.XPATH, ".//*[text()]")
            
            for text_elem in all_text_elements:
                text = text_elem.text.strip()
                if not text:
                    continue
                    
                tag_name = text_elem.tag_name
                classes = text_elem.get_attribute('class') or ''
                
                # Определяем, похож ли на название
                if len(text) > 10 and '₽' not in text and 'руб' not in text:
                    title_candidates.append({
                        'text': text,
                        'tag': tag_name,
                        'classes': classes,
                        'xpath': self.get_relative_xpath(elem, text_elem)
                    })
                
                # Определяем, похож ли на цену
                if '₽' in text or 'руб' in text or text.isdigit():
                    price_candidates.append({
                        'text': text,
                        'tag': tag_name,
                        'classes': classes,
                        'xpath': self.get_relative_xpath(elem, text_elem)
                    })
            
            print(f"   Кандидаты на название: {len(title_candidates)}")
            for tc in title_candidates[:3]:
                print(f"      📝 {tc['text'][:50]}... | {tc['tag']} | {tc['classes'][:30]}...")
                
            print(f"   Кандидаты на цену: {len(price_candidates)}")
            for pc in price_candidates[:3]:
                print(f"      💰 {pc['text']} | {pc['tag']} | {pc['classes'][:30]}...")
            
            # Сохраняем лучшие кандидаты
            if title_candidates:
                optimal_selectors['title'].extend([tc['xpath'] for tc in title_candidates[:2]])
            if price_candidates:
                optimal_selectors['price'].extend([pc['xpath'] for pc in price_candidates[:2]])
        
        # Убираем дубликаты и создаем финальные селекторы
        title_selectors = list(set(optimal_selectors['title']))
        price_selectors = list(set(optimal_selectors['price']))
        
        print(f"\n🎯 ОПТИМАЛЬНЫЕ СЕЛЕКТОРЫ:")
        print(f"\n📝 Названия ({len(title_selectors)}):")
        for i, selector in enumerate(title_selectors[:5]):
            print(f"   {i+1}. {selector}")
            
        print(f"\n💰 Цены ({len(price_selectors)}):")
        for i, selector in enumerate(price_selectors[:5]):
            print(f"   {i+1}. {selector}")
        
        # Тестируем скорость новых селекторов
        print(f"\n⚡ ТЕСТ СКОРОСТИ:")
        self.test_selector_speed(product_elements[:3], title_selectors[:3], price_selectors[:3])
        
        # Генерируем код для вставки
        self.generate_code(title_selectors[:5], price_selectors[:5])
    
    def get_relative_xpath(self, parent, child):
        """Получение относительного XPath от родителя к дочернему элементу"""
        try:
            # Простой способ - через тег и классы
            tag = child.tag_name
            classes = child.get_attribute('class')
            
            if classes:
                class_condition = " and ".join([f"contains(@class, '{cls}')" for cls in classes.split() if cls])
                if class_condition:
                    return f".//{tag}[{class_condition}]"
            
            # Если нет классов, используем текст
            text = child.text.strip()
            if text and len(text) < 50:
                return f".//{tag}[contains(text(), '{text[:20]}')]"
            
            return f".//{tag}"
        except:
            return f".//{child.tag_name}"
    
    def test_selector_speed(self, elements, title_selectors, price_selectors):
        """Тестирование скорости селекторов"""
        
        for i, elem in enumerate(elements):
            print(f"\n   Товар {i+1}:")
            
            # Тест названий
            title_found = False
            for j, selector in enumerate(title_selectors):
                start_time = time.time()
                try:
                    self.driver.implicitly_wait(1)
                    title_elem = elem.find_element(By.XPATH, selector)
                    title = title_elem.text.strip()
                    search_time = time.time() - start_time
                    
                    if title:
                        print(f"      📝 Селектор {j+1}: '{title[:30]}...' за {search_time:.3f}с")
                        title_found = True
                        break
                    else:
                        print(f"      📝 Селектор {j+1}: пустой за {search_time:.3f}с")
                except Exception as e:
                    search_time = time.time() - start_time
                    print(f"      📝 Селектор {j+1}: ошибка за {search_time:.3f}с")
                finally:
                    self.driver.implicitly_wait(3)
            
            if not title_found:
                print(f"      ❌ Название не найдено")
            
            # Тест цен
            price_found = False
            for j, selector in enumerate(price_selectors):
                start_time = time.time()
                try:
                    self.driver.implicitly_wait(1)
                    price_elem = elem.find_element(By.XPATH, selector)
                    price = price_elem.text.strip()
                    search_time = time.time() - start_time
                    
                    if price:
                        print(f"      💰 Селектор {j+1}: '{price}' за {search_time:.3f}с")
                        price_found = True
                        break
                    else:
                        print(f"      💰 Селектор {j+1}: пустой за {search_time:.3f}с")
                except Exception as e:
                    search_time = time.time() - start_time
                    print(f"      💰 Селектор {j+1}: ошибка за {search_time:.3f}с")
                finally:
                    self.driver.implicitly_wait(3)
            
            if not price_found:
                print(f"      ❌ Цена не найдена")
    
    def generate_code(self, title_selectors, price_selectors):
        """Генерация кода для вставки в парсер"""
        
        print(f"\n🔧 КОД ДЛЯ ВСТАВКИ В SINGLE_BUSINESS_PARSER.PY:")
        print("=" * 60)
        
        print("# Оптимизированные селекторы для business-full-items-grouped-view")
        print("if 'business-full-items-grouped-view__item' in str(elem.get_attribute('class') or ''):")
        
        print("    # Быстрые селекторы названий")
        print("    title_selectors = [")
        for selector in title_selectors:
            print(f'        "{selector}",')
        print("    ]")
        
        print("    # Быстрые селекторы цен")
        print("    price_selectors = [")
        for selector in price_selectors:
            print(f'        "{selector}",')
        print("    ]")
        
        print("else:")
        print("    # Оригинальные селекторы для других типов")
        print("    title_selectors = [...] # существующие селекторы")
        print("    price_selectors = [...] # существующие селекторы")
        
        print("=" * 60)
    
    def close(self):
        """Закрытие браузера"""
        if self.driver:
            self.driver.quit()

def main():
    url = "https://yandex.ru/maps/org/stomatologiya_kolomakinykh/63665148745/prices/?ll=39.684845%2C47.319277&z=15.97"
    
    analyzer = SmartSelectorsFix()
    
    try:
        analyzer.analyze_and_fix_selectors(url)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()
