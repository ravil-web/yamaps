#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from config import *

def find_main_link():
    """Поиск основной ссылки на предприятие"""
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
        print("🔍 Поиск основной ссылки...")
        driver.get(SEARCH_URL)
        time.sleep(5)
        
        # Прокрутка
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
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
            
            # Ищем ссылки на организации
            org_links = elem.find_elements(By.XPATH, ".//a[contains(@href, '/org/')]")
            print(f"   Ссылок на организации: {len(org_links)}")
            
            if org_links:
                for j, link in enumerate(org_links):
                    href = link.get_attribute('href')
                    class_name = link.get_attribute('class')
                    print(f"   Орг ссылка {j+1}: href='{href}', class='{class_name}'")
            
            # Ищем заголовок предприятия
            title_elements = elem.find_elements(By.XPATH, ".//*[contains(@class, 'title') or contains(@class, 'name') or contains(@class, 'header')]")
            print(f"   Элементов с title/name/header: {len(title_elements)}")
            
            for j, title_elem in enumerate(title_elements):
                class_name = title_elem.get_attribute('class')
                text = title_elem.text.strip()
                print(f"   Заголовок {j+1}: class='{class_name}', text='{text}'")
                
                # Ищем ссылки внутри заголовка
                title_links = title_elem.find_elements(By.XPATH, ".//a")
                if title_links:
                    for k, title_link in enumerate(title_links):
                        href = title_link.get_attribute('href')
                        link_class = title_link.get_attribute('class')
                        print(f"     Ссылка в заголовке {k+1}: href='{href}', class='{link_class}'")
        
        # Попробуем найти ссылки по другому селектору
        print("\n🔍 Поиск по альтернативным селекторам:")
        
        # Ищем все ссылки на организации на странице
        all_org_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/org/')]")
        print(f"   Всего ссылок на организации на странице: {len(all_org_links)}")
        
        unique_urls = set()
        for j, link in enumerate(all_org_links[:10], 1):
            href = link.get_attribute('href')
            class_name = link.get_attribute('class')
            text = link.text.strip()
            
            # Очищаем URL
            clean_url = href.split('/gallery/')[0].split('/reviews/')[0].split('/photos/')[0]
            if not clean_url.endswith('/'):
                clean_url += '/'
            
            if clean_url not in unique_urls:
                unique_urls.add(clean_url)
                print(f"   Уникальная ссылка {j}: href='{href}', class='{class_name}', text='{text}'")
                print(f"     Очищенный URL: {clean_url}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    find_main_link()
