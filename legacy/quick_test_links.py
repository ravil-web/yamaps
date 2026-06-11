#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from config import *

def test_links():
    """Быстрый тест для проверки ссылок"""
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.implicitly_wait(5)
    
    try:
        print("🔍 Тестирование ссылок...")
        driver.get(SEARCH_URL)
        time.sleep(5)
        
        # Прокрутка
        for i in range(3):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
        
        # Находим элементы предприятий
        elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'search-business-snippet-view')]")
        print(f"📊 Найдено элементов: {len(elements)}")
        
        # Проверяем первые 3 элемента
        for i, elem in enumerate(elements[:3], 1):
            print(f"\n🔍 Элемент {i}:")
            
            # Ищем все ссылки в элементе
            all_links = elem.find_elements(By.XPATH, ".//a")
            print(f"   Всего ссылок: {len(all_links)}")
            
            for j, link in enumerate(all_links):
                href = link.get_attribute('href')
                class_name = link.get_attribute('class')
                text = link.text.strip()
                print(f"   Ссылка {j+1}: href='{href}', class='{class_name}', text='{text}'")
            
            # Ищем конкретно ссылки с классом title
            title_links = elem.find_elements(By.XPATH, ".//a[contains(@class, 'title')]")
            print(f"   Ссылок с 'title': {len(title_links)}")
            
            # Ищем ссылки на организации
            org_links = elem.find_elements(By.XPATH, ".//a[contains(@href, '/org/')]")
            print(f"   Ссылок на организации: {len(org_links)}")
            
            if org_links:
                for j, link in enumerate(org_links):
                    href = link.get_attribute('href')
                    class_name = link.get_attribute('class')
                    print(f"   Орг ссылка {j+1}: href='{href}', class='{class_name}'")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_links()
