#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест исправленного парсера
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_fixed_parser():
    """Тест исправленного парсера"""
    print("🧪 Тест исправленного парсера")
    print("=" * 50)
    
    # Настройка браузера
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')
    
    try:
        driver = webdriver.Chrome(options=options)
        print("✅ Браузер запущен")
        
        # URL для тестирования
        test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/Ростов%20на%20дону%20суворовский%20стоматология/"
        print(f"📖 Переход: {test_url}")
        driver.get(test_url)
        
        # Ожидание загрузки
        print("⏳ Ожидание загрузки...")
        time.sleep(8)
        
        # Попытка переключения на список
        print("🔄 Попытка переключения на список...")
        list_view_selectors = [
            "//button[contains(@class, 'tabs-select-view__tab') and contains(@aria-label, 'Список')]",
            "//button[contains(@title, 'Список')]",
            "//button[contains(text(), 'Список')]",
            "//div[contains(@class, 'tabs-select-view')]//button[2]"
        ]
        
        list_button_found = False
        for selector in list_view_selectors:
            try:
                wait = WebDriverWait(driver, 3)
                button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                
                if button.is_displayed() and button.is_enabled():
                    print(f"✅ Найдена кнопка списка: {selector}")
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(3)
                    list_button_found = True
                    break
                    
            except Exception as e:
                print(f"❌ Селектор не сработал: {selector}")
                continue
        
        if not list_button_found:
            print("⚠️ Кнопка списка не найдена, продолжаем с картой")
        
        # Сохранение HTML для анализа
        with open('test_page_debug.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("💾 HTML сохранен в test_page_debug.html")
        
        # Поиск элементов предприятий
        print("\n🔍 Поиск элементов предприятий...")
        
        business_selectors = [
            "//div[contains(@class, 'search-snippet-view')]",
            "//li[contains(@class, 'search-snippet-view')]",
            "//div[contains(@class, 'business-snippet-view')]",
            "//div[contains(@class, 'search-business-snippet-view')]",
            "//li[contains(@class, 'serp-item')]",
            "//div[contains(@class, 'companies-list-item')]",
            "//div[contains(@class, 'search-result-item')]",
            "//div[contains(@class, 'search-placemark-view')]",
            "//ymaps[contains(@class, 'marker')]//div[contains(@class, 'search-placemark-view')]"
        ]
        
        best_elements = []
        best_selector = None
        
        for selector in business_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                print(f"📊 {selector}: {len(elements)} элементов")
                
                if len(elements) > len(best_elements):
                    best_elements = elements
                    best_selector = selector
                    
            except Exception as e:
                print(f"❌ Ошибка с селектором: {e}")
                continue
        
        print(f"\n✅ Лучший селектор: {best_selector}")
        print(f"📊 Найдено элементов: {len(best_elements)}")
        
        # Если мало элементов, выполняем прокрутку
        if len(best_elements) < 10:
            print("\n📜 Выполняем прокрутку для загрузки больше элементов...")
            
            for i in range(10):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Проверяем новые элементы
                new_elements = driver.find_elements(By.XPATH, best_selector) if best_selector else []
                if len(new_elements) > len(best_elements):
                    best_elements = new_elements
                    print(f"📊 После прокрутки {i+1}: {len(best_elements)} элементов")
                
                # Поиск кнопок "Показать еще"
                show_more_selectors = [
                    "//button[contains(text(), 'Показать еще')]",
                    "//button[contains(text(), 'Загрузить еще')]",
                    "//button[contains(text(), 'Еще')]"
                ]
                
                for show_selector in show_more_selectors:
                    try:
                        buttons = driver.find_elements(By.XPATH, show_selector)
                        for button in buttons:
                            if button.is_displayed() and button.is_enabled():
                                print(f"🔘 Нажимаем кнопку: {show_selector}")
                                driver.execute_script("arguments[0].click();", button)
                                time.sleep(3)
                                break
                    except:
                        continue
        
        # Поиск ссылок
        print(f"\n🔗 Поиск ссылок в {len(best_elements)} элементах...")
        
        found_urls = []
        link_selectors = [
            ".//a[contains(@class, 'link-overlay')]",
            ".//a[contains(@href, '/org/')]",
            ".//a[@href]"
        ]
        
        for i, element in enumerate(best_elements[:20]):  # Ограничиваем для теста
            try:
                for link_sel in link_selectors:
                    try:
                        links = element.find_elements(By.XPATH, link_sel)
                        for link in links:
                            href = link.get_attribute('href')
                            if href and '/org/' in href and href not in found_urls:
                                found_urls.append(href)
                                print(f"   ✅ URL {len(found_urls)}: {href}")
                                break
                        if found_urls and len(found_urls) > i:
                            break
                    except:
                        continue
                        
                if len(found_urls) >= 10:  # Для теста ограничиваем
                    break
                    
            except Exception as e:
                print(f"❌ Ошибка обработки элемента {i+1}: {e}")
                continue
        
        print(f"\n📊 РЕЗУЛЬТАТЫ ТЕСТА:")
        print(f"   🔍 Лучший селектор: {best_selector}")
        print(f"   📊 Найдено элементов: {len(best_elements)}")
        print(f"   🔗 Извлечено URL: {len(found_urls)}")
        
        if len(found_urls) >= 5:
            print("✅ ТЕСТ ПРОЙДЕН - найдено достаточно URL")
        else:
            print("⚠️ ТЕСТ ЧАСТИЧНО ПРОЙДЕН - найдено мало URL")
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        
    finally:
        if 'driver' in locals():
            driver.quit()
            print("🔚 Браузер закрыт")

if __name__ == "__main__":
    test_fixed_parser()
