#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Упрощенная диагностика парсера
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def debug_simple():
    """Простая диагностика"""
    print("🔧 Простая диагностика парсера")
    print("=" * 40)
    
    # Настройка браузера
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(options=options)
        print("✅ Браузер запущен")
        
        # Переход на страницу
        url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/"
        print(f"📖 Переход: {url}")
        driver.get(url)
        
        # Ожидание
        print("⏳ Ожидание 10 секунд...")
        time.sleep(10)
        
        # Прокрутка
        print("📜 Прокрутка...")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        
        # Поиск элементов
        print("🔍 Поиск элементов...")
        
        selectors_to_try = [
            "//div[contains(@class, 'search-snippet-view')]",
            "//li[contains(@class, 'serp-item')]", 
            "//div[contains(@class, 'business-snippet-view')]",
            "//div[contains(@class, 'search-business-snippet-view')]",
            "//*[contains(text(), 'стоматолог')]"
        ]
        
        found_any = False
        for i, selector in enumerate(selectors_to_try):
            try:
                elements = driver.find_elements(By.XPATH, selector)
                print(f"   Селектор {i+1}: {len(elements)} элементов - {selector}")
                if elements and not found_any:
                    found_any = True
                    print(f"   ✅ Первый рабочий селектор: {selector}")
                    
                    # Попробуем кликнуть по первому элементу
                    try:
                        first_elem = elements[0]
                        print(f"   📄 Текст первого элемента: {first_elem.text[:100]}...")
                        
                        print("   🖱️ Попытка клика...")
                        first_elem.click()
                        time.sleep(5)
                        
                        # Проверка карточки
                        card_selectors = [
                            "//div[contains(@class, 'business-card-view__main-wrapper')]",
                            "//h1[contains(@class, 'card-title-view__title')]"
                        ]
                        
                        for card_selector in card_selectors:
                            try:
                                card_elem = driver.find_element(By.XPATH, card_selector)
                                if card_elem.is_displayed():
                                    print(f"   ✅ Карточка найдена: {card_selector}")
                                    print(f"   📋 Текст карточки: {card_elem.text[:100]}...")
                                    break
                            except:
                                continue
                        
                    except Exception as e:
                        print(f"   ❌ Ошибка клика: {e}")
                        
            except Exception as e:
                print(f"   Селектор {i+1}: ошибка - {e}")
        
        if not found_any:
            print("❌ Ничего не найдено")
            print("💡 Попробуем найти любые элементы...")
            
            # Получим заголовок страницы
            title = driver.title
            print(f"📄 Заголовок страницы: {title}")
            
            # Поиск любых элементов с классами
            try:
                all_divs = driver.find_elements(By.TAG_NAME, "div")
                print(f"📊 Всего div элементов: {len(all_divs)}")
                
                # Найдем элементы с интересными классами
                interesting_classes = []
                for div in all_divs[:50]:  # Первые 50
                    class_attr = div.get_attribute('class')
                    if class_attr and ('search' in class_attr or 'snippet' in class_attr or 'business' in class_attr):
                        interesting_classes.append(class_attr)
                
                if interesting_classes:
                    print("🎯 Интересные классы:")
                    for cls in set(interesting_classes[:10]):
                        print(f"   - {cls}")
            except:
                pass
        
        print("\n👀 Браузер оставлен открытым")
        print("Изучите страницу вручную и нажмите Enter...")
        input()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    debug_simple()

