#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Интерактивный анализатор структуры Яндекс Карт
Открывает браузер и позволяет пошагово анализировать элементы
"""

import sys
import os
import time

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from src.browser_manager import BrowserManager
from selenium.webdriver.common.by import By

def interactive_analyzer():
    """Интерактивный анализ страницы"""
    print("🔍 Интерактивный анализатор структуры Яндекс Карт")
    print("=" * 60)
    
    config = Config()
    config.HEADLESS = False
    
    browser_manager = BrowserManager(config)
    
    try:
        print("🚀 Запуск браузера...")
        if not browser_manager.setup_driver():
            return
        
        driver = browser_manager.driver
        
        test_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/"
        print(f"📖 Переход: {test_url}")
        
        if not browser_manager.navigate_to_url(test_url):
            return
            
        print("⏳ Ожидание загрузки...")
        time.sleep(8)
        
        print("📜 Прокрутка...")
        browser_manager.scroll_page(max_scrolls=2)
        time.sleep(3)
        
        print("\n🎯 Анализ структуры:")
        print("-" * 40)
        
        # Шаг 1: Поиск списка результатов
        print("\n1️⃣ Поиск списка результатов:")
        list_selectors = [
            "//div[contains(@class, 'search-snippet-view')]",
            "//div[contains(@class, 'business-snippet-view')]", 
            "//li[contains(@class, 'serp-item')]",
            "//div[contains(@class, 'companies-list')]",
            "//div[contains(@class, 'search-result')]"
        ]
        
        found_results = None
        for i, selector in enumerate(list_selectors):
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"   ✅ Селектор {i+1}: {len(elements)} элементов - {selector}")
                    if not found_results:
                        found_results = elements
                        working_selector = selector
                else:
                    print(f"   ❌ Селектор {i+1}: 0 элементов - {selector}")
            except Exception as e:
                print(f"   ❌ Селектор {i+1}: ошибка - {e}")
        
        if not found_results:
            print("❌ Список результатов не найден!")
            print("\n💡 Попробуем найти любые элементы с текстом 'стоматолог':")
            try:
                text_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'стоматолог')]")
                for elem in text_elements[:5]:
                    try:
                        text = elem.text[:100]
                        tag = elem.tag_name
                        classes = elem.get_attribute('class')
                        print(f"   📄 {tag}.{classes}: {text}")
                    except:
                        pass
            except:
                pass
            
            print("\n👀 Браузер открыт для ручного анализа")
            input("Найдите элементы списка вручную и нажмите Enter...")
            return
        
        print(f"\n✅ Найдено {len(found_results)} результатов с селектором: {working_selector}")
        
        # Шаг 2: Анализ структуры первого элемента
        print("\n2️⃣ Анализ первого элемента:")
        first_element = found_results[0]
        
        # Поиск названия
        name_selectors = [
            ".//span[contains(@class, 'search-business-snippet-view__title')]",
            ".//a[contains(@class, 'search-snippet-view__title')]",
            ".//div[contains(@class, 'search-snippet-view__title')]",
            ".//span[contains(@class, 'business-snippet-view__name')]",
            ".//h3",
            ".//h2",
            ".//*[contains(@class, 'title')]",
            ".//*[contains(@class, 'name')]"
        ]
        
        found_name = None
        for i, selector in enumerate(name_selectors):
            try:
                name_elem = first_element.find_element(By.XPATH, selector)
                if name_elem.text.strip():
                    print(f"   ✅ Название {i+1}: '{name_elem.text.strip()}' - {selector}")
                    if not found_name:
                        found_name = name_elem.text.strip()
                        name_selector = selector
                else:
                    print(f"   ❌ Название {i+1}: пустой текст - {selector}")
            except:
                print(f"   ❌ Название {i+1}: не найден - {selector}")
        
        # Поиск адреса
        print("\n   📍 Поиск адреса:")
        address_selectors = [
            ".//span[contains(@class, 'search-business-snippet-view__address')]",
            ".//div[contains(@class, 'search-snippet-view__address')]",
            ".//span[contains(@class, 'business-snippet-view__address')]",
            ".//*[contains(@class, 'address')]"
        ]
        
        found_address = None
        for i, selector in enumerate(address_selectors):
            try:
                addr_elem = first_element.find_element(By.XPATH, selector)
                if addr_elem.text.strip():
                    print(f"   ✅ Адрес {i+1}: '{addr_elem.text.strip()}' - {selector}")
                    if not found_address:
                        found_address = addr_elem.text.strip()
                else:
                    print(f"   ❌ Адрес {i+1}: пустой текст - {selector}")
            except:
                print(f"   ❌ Адрес {i+1}: не найден - {selector}")
        
        # Шаг 3: Попытка клика
        if found_name:
            print(f"\n3️⃣ Попытка клика по '{found_name}':")
            
            # Поиск кликабельного элемента
            clickable_selectors = [
                ".//span[contains(@class, 'search-business-snippet-view__title')]",
                ".//a[contains(@class, 'search-snippet-view__title')]",
                ".//div[contains(@class, 'search-snippet-view__title')]",
                "."  # сам элемент
            ]
            
            clicked = False
            for i, selector in enumerate(clickable_selectors):
                try:
                    if selector == ".":
                        clickable = first_element
                    else:
                        clickable = first_element.find_element(By.XPATH, selector)
                    
                    if clickable.is_displayed():
                        print(f"   🖱️ Попытка клика {i+1}: {selector}")
                        clickable.click()
                        clicked = True
                        print(f"   ✅ Клик выполнен!")
                        break
                except Exception as e:
                    print(f"   ❌ Клик {i+1} не удался: {e}")
            
            if clicked:
                print("\n   ⏳ Ожидание загрузки карточки (5 сек)...")
                time.sleep(5)
                
                # Проверка появления карточки
                print("\n4️⃣ Проверка карточки предприятия:")
                card_selectors = [
                    "//div[contains(@class, 'business-card-view__main-wrapper')]",
                    "//h1[contains(@class, 'card-title-view__title')]",
                    "//div[contains(@class, 'business-contacts-view')]"
                ]
                
                card_found = False
                for i, selector in enumerate(card_selectors):
                    try:
                        card_elem = driver.find_element(By.XPATH, selector)
                        if card_elem.is_displayed():
                            print(f"   ✅ Карточка {i+1}: найдена - {selector}")
                            card_found = True
                            break
                    except:
                        print(f"   ❌ Карточка {i+1}: не найдена - {selector}")
                
                if card_found:
                    print("\n   🎉 УСПЕХ! Карточка открылась!")
                    
                    # Попытка извлечь данные из карточки
                    print("\n5️⃣ Извлечение данных из карточки:")
                    
                    # Название
                    try:
                        title_elem = driver.find_element(By.XPATH, "//h1[contains(@class, 'card-title-view__title')]")
                        print(f"   📋 Название: {title_elem.text.strip()}")
                    except:
                        print("   ❌ Название в карточке не найдено")
                    
                    # Адрес
                    try:
                        addr_elem = driver.find_element(By.XPATH, "//div[contains(@class, 'business-contacts-view__address-link')]")
                        print(f"   📍 Адрес: {addr_elem.text.strip()}")
                    except:
                        print("   ❌ Адрес в карточке не найден")
                    
                    # Телефон
                    try:
                        phone_elem = driver.find_element(By.XPATH, "//span[@itemprop='telephone']")
                        print(f"   📞 Телефон: {phone_elem.text.strip()}")
                    except:
                        print("   ❌ Телефон не найден")
                    
                    # Рейтинг
                    try:
                        rating_elem = driver.find_element(By.XPATH, "//span[contains(@class, 'business-rating-badge-view__rating-text')]")
                        print(f"   ⭐ Рейтинг: {rating_elem.text.strip()}")
                    except:
                        print("   ❌ Рейтинг не найден")
                    
                    print("\n✅ Анализ завершен успешно!")
                    print("📋 Селекторы для парсера:")
                    print(f"   - Список: {working_selector}")
                    print(f"   - Название: {name_selector if 'name_selector' in locals() else 'не найден'}")
                    print(f"   - Карточка: {card_selectors[0]}")
                
                else:
                    print("   ❌ Карточка не открылась")
            else:
                print("   ❌ Не удалось кликнуть ни по одному элементу")
        
        print("\n👀 Браузер оставлен открытым для дополнительного анализа")
        print("Нажмите Enter для закрытия...")
        input()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        browser_manager.close()

if __name__ == "__main__":
    interactive_analyzer()
