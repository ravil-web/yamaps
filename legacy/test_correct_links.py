#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест правильных ссылок card-title-view__title-link
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def test_correct_links():
    """Тест поиска правильных ссылок"""
    print("🧪 Тест поиска ссылок card-title-view__title-link")
    print("=" * 50)
    
    options = Options()
    options.add_argument('--start-maximized')
    
    try:
        driver = webdriver.Chrome(options=options)
        print("✅ Браузер запущен")
        
        # URL из конфига
        from config import SEARCH_URL
        print(f"📖 Переход: {SEARCH_URL}")
        driver.get(SEARCH_URL)
        
        print("⏳ Ожидание загрузки...")
        time.sleep(8)
        
        # Прокрутка
        print("📜 Прокрутка...")
        for i in range(15):
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(1)
        
        # Сохранение HTML
        with open('test_correct_links_debug.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("💾 HTML сохранен в test_correct_links_debug.html")
        
        # Тест 1: Поиск точных ссылок card-title-view__title-link
        print("\n🔍 Тест 1: Поиск ссылок card-title-view__title-link")
        title_links = driver.find_elements(By.CSS_SELECTOR, "a.card-title-view__title-link[href*='/maps/org/']")
        print(f"📊 Найдено: {len(title_links)}")
        
        if title_links:
            print("✅ Первые 5 ссылок:")
            for i, link in enumerate(title_links[:5]):
                try:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    print(f"   {i+1}. {text}: {href}")
                except:
                    print(f"   {i+1}. Ошибка получения данных")
        
        # Тест 2: Поиск всех ссылок с /maps/org/
        print("\n🔍 Тест 2: Поиск всех ссылок с /maps/org/")
        maps_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/maps/org/')]")
        print(f"📊 Найдено: {len(maps_links)}")
        
        if maps_links:
            print("✅ Первые 5 ссылок:")
            for i, link in enumerate(maps_links[:5]):
                try:
                    href = link.get_attribute('href')
                    text = link.text.strip() or "Без текста"
                    print(f"   {i+1}. {text}: {href}")
                except:
                    print(f"   {i+1}. Ошибка получения данных")
        
        # Тест 3: Поиск всех ссылок с /org/
        print("\n🔍 Тест 3: Поиск всех ссылок с /org/")
        org_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/org/')]")
        print(f"📊 Найдено: {len(org_links)}")
        
        if org_links:
            print("✅ Первые 5 ссылок:")
            for i, link in enumerate(org_links[:5]):
                try:
                    href = link.get_attribute('href')
                    text = link.text.strip() or "Без текста"
                    # Преобразуем относительные ссылки в абсолютные
                    if href.startswith('/maps/org/'):
                        full_url = f"https://yandex.ru{href}"
                    else:
                        full_url = href
                    print(f"   {i+1}. {text}: {full_url}")
                except:
                    print(f"   {i+1}. Ошибка получения данных")
        
        # Итоги
        print(f"\n📊 РЕЗУЛЬТАТЫ:")
        print(f"   card-title-view__title-link: {len(title_links)}")
        print(f"   /maps/org/: {len(maps_links)}")
        print(f"   /org/: {len(org_links)}")
        
        best_count = max(len(title_links), len(maps_links), len(org_links))
        if best_count >= 5:
            print(f"✅ ТЕСТ ПРОЙДЕН - найдено {best_count} ссылок")
        else:
            print(f"⚠️ ТЕСТ ЧАСТИЧНО ПРОЙДЕН - найдено {best_count} ссылок")
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        
    finally:
        if 'driver' in locals():
            driver.quit()
            print("🔚 Браузер закрыт")

if __name__ == "__main__":
    test_correct_links()
