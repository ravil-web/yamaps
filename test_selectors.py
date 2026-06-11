#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест правильных селекторов
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_correct_selectors():
    """Тест правильных селекторов"""
    print("🧪 Тест правильных селекторов")
    print("=" * 50)
    
    # Настройка браузера
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')
    
    try:
        driver = webdriver.Chrome(options=options)
        print("✅ Браузер запущен")
        
        # URL для тестирования из config
        from config import SEARCH_URL
        print(f"📖 Переход: {SEARCH_URL}")
        driver.get(SEARCH_URL)
        
        # Ожидание загрузки
        print("⏳ Ожидание загрузки...")
        time.sleep(10)
        
        # Сохранение HTML
        with open('test_selectors_debug.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("💾 HTML сохранен в test_selectors_debug.html")
        
        # Тест 1: Поиск контейнера списка
        print("\n🔍 Тест 1: Поиск контейнера search-list-view__list")
        try:
            wait = WebDriverWait(driver, 10)
            list_container = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-list-view__list")))
            print(f"✅ Контейнер найден: {list_container.tag_name}")
            
            # Проверяем размеры контейнера
            size = list_container.size
            print(f"📏 Размер контейнера: {size['width']}x{size['height']}")
            
        except Exception as e:
            print(f"❌ Контейнер search-list-view__list не найден: {e}")
            
            # Попробуем альтернативные селекторы
            alt_selectors = [
                "search-list-view",
                "search-results", 
                "business-list",
                "search-snippet-view"
            ]
            
            for selector in alt_selectors:
                try:
                    elements = driver.find_elements(By.CLASS_NAME, selector)
                    if elements:
                        print(f"✅ Альтернативный контейнер найден: {selector} ({len(elements)} элементов)")
                        list_container = elements[0]
                        break
                except:
                    continue
        
        # Тест 2: Поиск ссылок на предприятия
        print("\n🔍 Тест 2: Поиск ссылок card-title-view__title-link")
        
        # Прокрутка для загрузки контента
        print("📜 Прокрутка для загрузки...")
        for i in range(5):
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(2)
            
            # Если есть контейнер, прокручиваем его тоже
            if 'list_container' in locals():
                try:
                    driver.execute_script("arguments[0].scrollTop += 500;", list_container)
                except:
                    pass
        
        # Поиск ссылок с точным селектором
        links = driver.find_elements(By.CSS_SELECTOR, "a.card-title-view__title-link[href*='/maps/org/']")
        print(f"📊 Найдено ссылок с card-title-view__title-link: {len(links)}")
        
        if links:
            print("✅ Первые 5 ссылок:")
            for i, link in enumerate(links[:5]):
                try:
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    print(f"   {i+1}. {text}: {href}")
                except:
                    print(f"   {i+1}. Ошибка получения данных ссылки")
        else:
            print("❌ Ссылки card-title-view__title-link не найдены")
            
            # Поиск альтернативных ссылок
            print("\n🔍 Поиск альтернативных ссылок...")
            
            alt_link_selectors = [
                "a[href*='/maps/org/']",
                "a[href*='/org/']", 
                ".business-link",
                ".organization-link"
            ]
            
            for selector in alt_link_selectors:
                try:
                    alt_links = driver.find_elements(By.CSS_SELECTOR, selector)
                    if alt_links:
                        print(f"✅ Альтернативные ссылки найдены: {selector} ({len(alt_links)} элементов)")
                        print("   Первые 3 ссылки:")
                        for i, link in enumerate(alt_links[:3]):
                            try:
                                href = link.get_attribute('href')
                                text = link.text.strip() or "Без текста"
                                print(f"      {i+1}. {text}: {href}")
                            except:
                                pass
                        break
                except:
                    continue
        
        # Тест 3: Проверка общей структуры
        print("\n🔍 Тест 3: Общая диагностика")
        
        # Все ссылки на странице
        all_links = driver.find_elements(By.TAG_NAME, "a")
        org_links = [link for link in all_links if '/org/' in (link.get_attribute('href') or '')]
        
        print(f"📊 Всего ссылок на странице: {len(all_links)}")
        print(f"📊 Ссылок с '/org/': {len(org_links)}")
        
        # Элементы с классами, содержащими 'card'
        card_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'card')]")
        print(f"📊 Элементов с 'card' в классе: {len(card_elements)}")
        
        # Элементы с классами, содержащими 'business'
        business_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'business')]")
        print(f"📊 Элементов с 'business' в классе: {len(business_elements)}")
        
        # Элементы с классами, содержащими 'search'
        search_elements = driver.find_elements(By.XPATH, "//*[contains(@class, 'search')]")
        print(f"📊 Элементов с 'search' в классе: {len(search_elements)}")
        
        print("\n📊 РЕЗУЛЬТАТЫ ТЕСТА:")
        if len(links) > 0:
            print(f"✅ ТЕСТ ПРОЙДЕН - найдено {len(links)} ссылок с правильным селектором")
        elif len(org_links) > 0:
            print(f"⚠️ ТЕСТ ЧАСТИЧНО ПРОЙДЕН - найдено {len(org_links)} альтернативных ссылок")
        else:
            print("❌ ТЕСТ НЕ ПРОЙДЕН - ссылки не найдены")
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        
    finally:
        if 'driver' in locals():
            driver.quit()
            print("🔚 Браузер закрыт")

if __name__ == "__main__":
    test_correct_selectors()
