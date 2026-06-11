#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Диагностический скрипт для анализа медленного парсинга товаров
"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

class SlowParsingAnalyzer:
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
        self.driver.implicitly_wait(5)
    
    def analyze_page(self, url):
        """Анализ страницы предприятия"""
        print(f"🔍 Анализируем: {url}")
        
        self.driver.get(url)
        time.sleep(5)
        
        # Переход на вкладку товаров
        self.try_switch_to_products_tab()
        
        # Анализ селекторов
        selectors_analysis = self.analyze_selectors()
        
        # Анализ производительности
        performance_analysis = self.analyze_performance()
        
        # Сохранение HTML
        self.save_debug_html(url)
        
        return {
            'url': url,
            'selectors': selectors_analysis,
            'performance': performance_analysis,
            'timestamp': time.time()
        }
    
    def try_switch_to_products_tab(self):
        """Попытка перехода на вкладку товаров"""
        tab_selectors = [
            "//div[@class='tabs-select-view__title _name_prices']",
            "//div[contains(@class, 'tabs-select-view__title') and contains(text(), 'Цены')]",
            "//div[contains(@class, 'tabs-select-view__title') and contains(text(), 'Товары')]",
            "//div[contains(@class, 'tabs-select-view__title') and contains(text(), 'Услуги')]",
        ]
        
        for selector in tab_selectors:
            try:
                tab_elem = self.driver.find_element(By.XPATH, selector)
                self.driver.execute_script("arguments[0].click();", tab_elem)
                time.sleep(2)
                print(f"   ✅ Перешли на вкладку товаров: {selector}")
                return True
            except:
                continue
        
        print("   ⚠️ Вкладка товаров не найдена")
        return False
    
    def analyze_selectors(self):
        """Анализ производительности селекторов"""
        selectors = [
            "//div[contains(@class, 'business-full-items-grouped-view__item')]",
            "//div[contains(@class, 'related-item-photo-view')]",
            "//div[contains(@class, 'related-item-list-view__item')]", 
            "//div[contains(@class, 'related-product-view')]",
            "//div[contains(@class, 'product-item')]",
            "//div[contains(@class, 'service-item')]", 
            "//div[contains(@class, 'price-item')]",
            "//div[contains(@class, 'menu-item')]",
        ]
        
        results = {}
        
        for selector in selectors:
            start_time = time.time()
            try:
                elems = self.driver.find_elements(By.XPATH, selector)
                search_time = time.time() - start_time
                
                results[selector] = {
                    'count': len(elems),
                    'search_time': search_time,
                    'found': len(elems) > 0
                }
                
                print(f"   📊 {selector}: {len(elems)} элементов за {search_time:.3f}с")
                
            except Exception as e:
                results[selector] = {
                    'count': 0,
                    'search_time': time.time() - start_time,
                    'error': str(e),
                    'found': False
                }
        
        return results
    
    def analyze_performance(self):
        """Анализ производительности извлечения данных"""
        # Находим первые 5 товаров для тестирования
        all_selectors = [
            "//div[contains(@class, 'business-full-items-grouped-view__item')]",
            "//div[contains(@class, 'related-item-photo-view')]",
            "//div[contains(@class, 'related-item-list-view__item')]", 
            "//div[contains(@class, 'related-product-view')]",
        ]
        
        test_elems = []
        used_selector = None
        
        for selector in all_selectors:
            try:
                elems = self.driver.find_elements(By.XPATH, selector)
                if elems:
                    test_elems = elems[:5]  # Тестируем первые 5
                    used_selector = selector
                    break
            except:
                continue
        
        if not test_elems:
            return {'error': 'Не найдено товаров для тестирования'}
        
        print(f"   🧪 Тестируем производительность с селектором: {used_selector}")
        
        # Тестируем извлечение данных
        title_selectors = [
            ".//div[contains(@class, 'related-item-photo-view__title')]",
            ".//div[contains(@class, 'related-item-list-view__title')]",
            ".//div[contains(@class, 'product-title')]",
            ".//div[contains(@class, 'service-title')]",
            ".//div[contains(@class, 'item-title')]",
            ".//span[contains(@class, 'title')]",
            ".//div[contains(@class, 'title')]",
        ]
        
        price_selectors = [
            ".//span[contains(@class, 'related-product-view__price')]",
            ".//div[contains(@class, 'related-product-view__price')]",
            ".//span[contains(@class, 'price')]",
            ".//div[contains(@class, 'price')]",
        ]
        
        performance_data = {
            'used_selector': used_selector,
            'total_elements': len(test_elems),
            'extraction_times': []
        }
        
        for i, elem in enumerate(test_elems):
            start_time = time.time()
            
            # Поиск названия
            title = ""
            title_time = 0
            title_start = time.time()
            for selector in title_selectors:
                try:
                    title_elem = elem.find_element(By.XPATH, selector)
                    title = title_elem.text.strip()
                    if title:
                        break
                except:
                    continue
            title_time = time.time() - title_start
            
            # Поиск цены
            price = ""
            price_time = 0
            price_start = time.time()
            for selector in price_selectors:
                try:
                    price_elem = elem.find_element(By.XPATH, selector)
                    price = price_elem.text.strip()
                    if price:
                        break
                except:
                    continue
            price_time = time.time() - price_start
            
            total_time = time.time() - start_time
            
            extraction_data = {
                'item_index': i + 1,
                'title': title,
                'price': price,
                'title_time': title_time,
                'price_time': price_time,
                'total_time': total_time
            }
            
            performance_data['extraction_times'].append(extraction_data)
            print(f"      Товар {i+1}: {title} - {price} (за {total_time:.3f}с)")
        
        avg_time = sum(item['total_time'] for item in performance_data['extraction_times']) / len(performance_data['extraction_times'])
        performance_data['average_time_per_item'] = avg_time
        
        print(f"   ⚡ Среднее время на товар: {avg_time:.3f}с")
        
        return performance_data
    
    def save_debug_html(self, url):
        """Сохранение HTML страницы для анализа"""
        # Получаем название предприятия для имени файла
        try:
            name_elem = self.driver.find_element(By.XPATH, "//h1")
            business_name = name_elem.text.strip()
            safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in business_name)
            safe_name = safe_name.replace(' ', '_')[:50]
        except:
            safe_name = "unknown_business"
        
        filename = f"debug_slow_parsing_{safe_name}_{int(time.time())}.html"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(self.driver.page_source)
        
        print(f"   💾 HTML сохранен: {filename}")
        return filename
    
    def close(self):
        """Закрытие браузера"""
        if self.driver:
            self.driver.quit()

def main():
    print("🔍 ДИАГНОСТИКА МЕДЛЕННОГО ПАРСИНГА")
    print("=" * 50)
    
    # URL для тестирования (замените на URL медленного предприятия)
    slow_url = input("📝 Введите URL медленного предприятия: ").strip()
    
    if not slow_url:
        print("❌ URL не введен")
        return
    
    analyzer = SlowParsingAnalyzer()
    
    try:
        results = analyzer.analyze_page(slow_url)
        
        # Сохраняем результаты
        with open(f"slow_parsing_analysis_{int(time.time())}.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print("\n🎯 РЕКОМЕНДАЦИИ:")
        
        # Анализ результатов
        best_selector = None
        best_time = float('inf')
        
        for selector, data in results['selectors'].items():
            if data['found'] and data['count'] > 0:
                if data['search_time'] < best_time:
                    best_time = data['search_time']
                    best_selector = selector
        
        if best_selector:
            print(f"✅ Лучший селектор: {best_selector}")
            print(f"   Время поиска: {best_time:.3f}с")
            print(f"   Найдено элементов: {results['selectors'][best_selector]['count']}")
        
        if 'performance' in results and 'average_time_per_item' in results['performance']:
            avg_time = results['performance']['average_time_per_item']
            if avg_time > 1.0:
                print(f"⚠️ Медленное извлечение данных: {avg_time:.3f}с на товар")
                print("   Рекомендуется оптимизировать селекторы для извлечения названий и цен")
            else:
                print(f"✅ Нормальная скорость извлечения: {avg_time:.3f}с на товар")
        
    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
    
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()
