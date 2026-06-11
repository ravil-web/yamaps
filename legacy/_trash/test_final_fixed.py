#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Быстрый тест исправленного финального парсера
"""

import time
import os
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

class QuickTest:
    def __init__(self):
        self.driver = None
        self.businesses = []
    
    def setup_driver(self):
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.implicitly_wait(5)
        return True
    
    def extract_business_data(self):
        """Извлечение данных с исправленными селекторами"""
        data = {
            'name': '',
            'verified': False,
            'categories': [],
            'rating': '',
            'reviews_count': '',
            'address': '',
            'phones': [],
            'website': '',
            'url': self.driver.current_url,
            'last_updated': datetime.now().isoformat()
        }
        
        # НАЗВАНИЕ (исправленные селекторы)
        try:
            name_selectors = [
                "//h1",
                "//*[@itemprop='name']",
                "//meta[@property='og:title']"
            ]
            for selector in name_selectors:
                try:
                    if 'meta' in selector:
                        name_elem = self.driver.find_element(By.XPATH, selector)
                        full_title = name_elem.get_attribute('content')
                        if full_title and ',' in full_title:
                            data['name'] = full_title.split(',')[0].strip()
                        elif full_title:
                            data['name'] = full_title.strip()
                    else:
                        name_elem = self.driver.find_element(By.XPATH, selector)
                        text = name_elem.text.strip() if name_elem.text else ""
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
        
        # РЕЙТИНГ
        try:
            rating_elem = self.driver.find_element(By.XPATH, "//span[contains(@class, 'business-rating-badge-view__rating-text')]")
            data['rating'] = rating_elem.text.strip() if rating_elem.text else ""
        except:
            pass
        
        # АДРЕС
        try:
            address_elem = self.driver.find_element(By.XPATH, "//div[contains(@class, 'business-contacts-view__address-link')]")
            data['address'] = address_elem.text.strip() if address_elem.text else ""
        except:
            pass
        
        print(f"✅ Извлечены данные: {data['name']}")
        return data
    
    def test_extraction(self):
        """Тест извлечения данных"""
        urls = [
            "https://yandex.ru/maps/org/estetika/164194457137/",
            "https://yandex.ru/maps/org/dentalkea/131230205132/",
            "https://yandex.ru/maps/org/milan/1078009594/"
        ]
        
        print("🚀 ТЕСТ ИСПРАВЛЕННОГО ПАРСЕРА")
        print("=" * 50)
        
        for i, url in enumerate(urls):
            print(f"\n📍 Предприятие {i+1}/3")
            print(f"🎯 URL: {url}")
            
            self.driver.get(url)
            time.sleep(5)
            
            business_data = self.extract_business_data()
            
            if business_data['name']:
                self.businesses.append(business_data)
                print(f"   ✅ Название: {business_data['name']}")
                print(f"   🏷️ Верифицирован: {business_data['verified']}")
                print(f"   ⭐ Рейтинг: {business_data['rating']}")
                print(f"   📍 Адрес: {business_data['address'][:50]}...")
            else:
                print("   ❌ Название не извлечено")
        
        # Результаты
        print(f"\n📈 РЕЗУЛЬТАТЫ:")
        print(f"   Успешно обработано: {len(self.businesses)}/3")
        
        if len(self.businesses) == 3:
            print("   ✅ ТЕСТ ПРОЙДЕН - все названия извлечены!")
            
            # Сохраняем результат
            os.makedirs("output", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"output/test_results_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.businesses, f, ensure_ascii=False, indent=2)
            
            print(f"   💾 Результаты сохранены: {filename}")
            
        else:
            print("   ❌ ТЕСТ НЕ ПРОЙДЕН")
        
        input("\nНажмите Enter для закрытия...")
        self.driver.quit()

def main():
    tester = QuickTest()
    tester.setup_driver()
    tester.test_extraction()

if __name__ == "__main__":
    main()
