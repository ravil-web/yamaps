#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from config import *

def analyze_page_structure():
    """Анализ структуры страницы поиска"""
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
        print("🔍 Анализ структуры страницы поиска...")
        print(f"📄 URL: {SEARCH_URL}")
        
        driver.get(SEARCH_URL)
        time.sleep(5)
        
        # Прокрутка для загрузки результатов
        print("📜 Прокрутка страницы...")
        for i in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
        
        print("\n" + "="*80)
        print("АНАЛИЗ СТРУКТУРЫ СТРАНИЦЫ")
        print("="*80)
        
        # Поиск всех ссылок на организации
        print("\n🔍 Поиск всех ссылок на организации:")
        org_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/org/')]")
        print(f"📊 Найдено ссылок на организации: {len(org_links)}")
        
        unique_urls = set()
        for i, link in enumerate(org_links[:10], 1):  # Показываем первые 10
            url = link.get_attribute('href')
            if url:
                clean_url = url.split('/gallery/')[0].split('/reviews/')[0].split('/photos/')[0]
                if not clean_url.endswith('/'):
                    clean_url += '/'
                unique_urls.add(clean_url)
                print(f"   {i}. {clean_url}")
        
        print(f"\n📊 Уникальных URL: {len(unique_urls)}")
        
        # Поиск элементов предприятий
        print("\n🔍 Поиск элементов предприятий:")
        selectors = [
            "//div[contains(@class, 'search-business-snippet-view')]",
            "//div[contains(@class, 'search-result-item-view')]",
            "//div[contains(@class, 'business-snippet-view')]",
            "//div[contains(@class, 'search-result')]",
            "//div[contains(@class, 'business-item')]",
            "//div[contains(@class, 'search-item')]",
            "//div[contains(@class, 'search-list-item')]",
            "//div[contains(@class, 'list-item')]",
            "//div[contains(@class, 'item') and contains(@class, 'search')]",
            "//div[contains(@class, 'search-list')]//div[contains(@class, 'item')]",
            "//div[contains(@class, 'search-results')]//div[contains(@class, 'item')]"
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"✅ '{selector}': {len(elements)} элементов")
                    
                    # Проверим первые 3 элемента
                    for i, elem in enumerate(elements[:3], 1):
                        try:
                            # Ищем ссылки внутри элемента
                            links = elem.find_elements(By.XPATH, ".//a[contains(@href, '/org/')]")
                            if links:
                                url = links[0].get_attribute('href')
                                clean_url = url.split('/gallery/')[0].split('/reviews/')[0].split('/photos/')[0]
                                if not clean_url.endswith('/'):
                                    clean_url += '/'
                                print(f"   Элемент {i}: {clean_url}")
                            else:
                                print(f"   Элемент {i}: ссылки не найдены")
                        except Exception as e:
                            print(f"   Элемент {i}: ошибка - {e}")
                    break
                else:
                    print(f"❌ '{selector}': элементов не найдено")
            except Exception as e:
                print(f"❌ '{selector}': ошибка - {e}")
        
        # Анализ HTML структуры
        print("\n🔍 Анализ HTML структуры:")
        try:
            # Ищем контейнер с результатами поиска
            search_containers = [
                "//div[contains(@class, 'search-list')]",
                "//div[contains(@class, 'search-results')]",
                "//div[contains(@class, 'results')]",
                "//div[contains(@class, 'list')]"
            ]
            
            for container_selector in search_containers:
                try:
                    container = driver.find_element(By.XPATH, container_selector)
                    print(f"✅ Найден контейнер: '{container_selector}'")
                    
                    # Ищем элементы внутри контейнера
                    items = container.find_elements(By.XPATH, ".//div[contains(@class, 'item')]")
                    print(f"   Элементов в контейнере: {len(items)}")
                    
                    if items:
                        for i, item in enumerate(items[:3], 1):
                            try:
                                links = item.find_elements(By.XPATH, ".//a[contains(@href, '/org/')]")
                                if links:
                                    url = links[0].get_attribute('href')
                                    clean_url = url.split('/gallery/')[0].split('/reviews/')[0].split('/photos/')[0]
                                    if not clean_url.endswith('/'):
                                        clean_url += '/'
                                    print(f"   Элемент {i}: {clean_url}")
                                else:
                                    print(f"   Элемент {i}: ссылки не найдены")
                            except Exception as e:
                                print(f"   Элемент {i}: ошибка - {e}")
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"❌ Ошибка анализа HTML: {e}")
        
        # Сохранение HTML для анализа
        print("\n💾 Сохранение HTML страницы...")
        with open('page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("✅ HTML сохранен в файл 'page_source.html'")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    analyze_page_structure()
