#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from config import *

def debug_page_structure():
    """Диагностика структуры страницы поиска"""
    
    # Настройка WebDriver
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    driver.implicitly_wait(5)
    
    try:
        print("🔍 Загрузка страницы поиска...")
        driver.get(SEARCH_URL)
        time.sleep(5)
        
        print("\n" + "="*80)
        print("АНАЛИЗ СТРУКТУРЫ СТРАНИЦЫ")
        print("="*80)
        
        # 1. Анализ всех элементов с классом search-business-snippet-view
        print("\n1. ЭЛЕМЕНТЫ search-business-snippet-view:")
        elements = driver.find_elements(By.XPATH, "//div[contains(@class, 'search-business-snippet-view')]")
        print(f"   Найдено: {len(elements)}")
        
        for i, elem in enumerate(elements[:10], 1):  # Показываем первые 10
            try:
                # Ищем ссылку внутри элемента
                link = elem.find_element(By.XPATH, ".//a[contains(@href, '/org/')]")
                href = link.get_attribute('href')
                print(f"   {i}. {href}")
            except:
                print(f"   {i}. Ссылка не найдена")
        
        # 2. Анализ всех ссылок link-overlay
        print("\n2. ССЫЛКИ link-overlay:")
        overlay_links = driver.find_elements(By.XPATH, "//a[contains(@class, 'link-overlay')]")
        print(f"   Найдено: {len(overlay_links)}")
        
        for i, link in enumerate(overlay_links[:10], 1):
            href = link.get_attribute('href')
            print(f"   {i}. {href}")
        
        # 3. Анализ всех ссылок с /org/
        print("\n3. ВСЕ ССЫЛКИ С /org/:")
        org_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/org/')]")
        print(f"   Найдено: {len(org_links)}")
        
        for i, link in enumerate(org_links[:15], 1):
            href = link.get_attribute('href')
            print(f"   {i}. {href}")
        
        # 4. Анализ элементов списка
        print("\n4. ЭЛЕМЕНТЫ СПИСКА:")
        list_items = driver.find_elements(By.XPATH, "//li[@class='search-snippet-view']")
        print(f"   Найдено: {len(list_items)}")
        
        # 5. Анализ контейнера списка
        print("\n5. КОНТЕЙНЕР СПИСКА:")
        containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'search-list-view__content')]")
        print(f"   Найдено контейнеров: {len(containers)}")
        
        if containers:
            container = containers[0]
            print(f"   Высота контейнера: {container.size['height']}")
            print(f"   Прокрутка контейнера: {driver.execute_script('return arguments[0].scrollHeight', container)}")
        
        # 6. Прокрутка и повторный анализ
        print("\n6. ПОСЛЕ ПРОКРУТКИ:")
        
        # Прокручиваем страницу
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # Повторно анализируем
        elements_after = driver.find_elements(By.XPATH, "//div[contains(@class, 'search-business-snippet-view')]")
        overlay_after = driver.find_elements(By.XPATH, "//a[contains(@class, 'link-overlay')]")
        org_after = driver.find_elements(By.XPATH, "//a[contains(@href, '/org/')]")
        
        print(f"   Элементов после прокрутки: {len(elements_after)}")
        print(f"   Ссылок link-overlay после прокрутки: {len(overlay_after)}")
        print(f"   Ссылок /org/ после прокрутки: {len(org_after)}")
        
        # 7. Поиск кнопок "Показать еще"
        print("\n7. КНОПКИ 'ПОКАЗАТЬ ЕЩЕ':")
        show_more_selectors = [
            "//button[contains(text(), 'Показать еще')]",
            "//button[contains(text(), 'Загрузить еще')]",
            "//button[contains(text(), 'Еще')]",
            "//button[contains(@class, 'show-more')]",
            "//button[contains(@class, 'load-more')]",
            "//a[contains(text(), 'Показать еще')]",
            "//a[contains(text(), 'Загрузить еще')]"
        ]
        
        for selector in show_more_selectors:
            buttons = driver.find_elements(By.XPATH, selector)
            if buttons:
                print(f"   Найдено кнопок '{selector}': {len(buttons)}")
                for btn in buttons:
                    print(f"     - Текст: '{btn.text}', Видима: {btn.is_displayed()}")
        
        # 8. Анализ HTML структуры
        print("\n8. HTML СТРУКТУРА (первые 2000 символов):")
        page_source = driver.page_source
        print(page_source[:2000])
        
        print("\n" + "="*80)
        print("ДИАГНОСТИКА ЗАВЕРШЕНА")
        print("="*80)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    debug_page_structure()
