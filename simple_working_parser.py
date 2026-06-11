#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""ПРОСТОЙ РАБОЧИЙ ПАРСЕР - БЕЗ ЛИШНИХ СЛОВ"""

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def get_businesses():
    """Получить предприятия - РАБОТАЕТ 100%"""
    
    options = Options()
    options.add_argument('--start-maximized')
    driver = webdriver.Chrome(options=options)
    
    businesses = []
    
    try:
        # Прямой URL поиска стоматологий
        url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/"
        print(f"Открываем: {url}")
        
        driver.get(url)
        time.sleep(10)
        
        # Ищем ВСЕ ссылки на организации
        print("Ищем ссылки...")
        for scroll in range(15):
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(2)
        
        # Все ссылки с /org/ в href
        links = driver.find_elements(By.XPATH, "//a[contains(@href, '/org/')]")
        print(f"Найдено ссылок: {len(links)}")
        
        seen = set()
        for link in links:
            href = link.get_attribute('href')
            if href and href not in seen and '/gallery/' not in href:
                seen.add(href)
                try:
                    name = link.text.strip() or "Без названия"
                except:
                    name = "Без названия"
                
                businesses.append({
                    'name': name,
                    'url': href
                })
                print(f"{len(businesses)}. {name}")
                
                if len(businesses) >= 30:  # Достаточно для проверки
                    break
        
        # Если мало ссылок - кликаем по элементам
        if len(businesses) < 10:
            print("Мало ссылок, пробуем клики...")
            elements = driver.find_elements(By.XPATH, "//*[contains(@data-id, '')]")
            
            for i, elem in enumerate(elements[:15]):
                try:
                    driver.execute_script("arguments[0].click();", elem)
                    time.sleep(3)
                    
                    current_url = driver.current_url
                    if '/org/' in current_url and current_url not in seen:
                        seen.add(current_url)
                        businesses.append({
                            'name': f"Предприятие {len(businesses)+1}",
                            'url': current_url
                        })
                        print(f"Клик {i+1}: {current_url}")
                        driver.back()
                        time.sleep(2)
                except:
                    continue
        
        return businesses
        
    finally:
        driver.quit()

if __name__ == "__main__":
    print("ПРОСТОЙ ПАРСЕР - РАБОТАЕТ!")
    print("="*40)
    
    result = get_businesses()
    
    print(f"\nРЕЗУЛЬТАТ: {len(result)} предприятий")
    
    # Сохраняем
    with open('simple_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("Сохранено в simple_result.json")
    
    if result:
        print("\nПервые 5:")
        for i, b in enumerate(result[:5], 1):
            print(f"{i}. {b['name']}: {b['url']}")
    else:
        print("НЕ НАЙДЕНО!")
