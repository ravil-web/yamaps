#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Простой тест клика по первому предприятию
"""

import sys
import os
import time

# Добавление пути к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from src.browser_manager import BrowserManager
from selenium.webdriver.common.by import By

def simple_click_test():
    """Простой тест клика по предприятию"""
    print("🎯 Простой тест клика по предприятию")
    print("=" * 50)
    
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
        
        # Поиск первого предприятия
        print("🔍 Поиск предприятий...")
        selectors = [
            "//div[contains(@class, 'search-snippet-view')]",
            "//div[contains(@class, 'business-snippet-view')]",
            "//li[contains(@class, 'serp-item')]"
        ]
        
        found_businesses = []
        for i, selector in enumerate(selectors):
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if elements:
                    found_businesses = elements
                    print(f"✅ Найдено {len(elements)} предприятий с селектором {i+1}")
                    break
            except Exception as e:
                print(f"❌ Селектор {i+1} не сработал: {e}")
        
        if not found_businesses:
            print("❌ Предприятия не найдены")
            return
        
        # Попытка клика по первому предприятию
        print("🎯 Попытка клика по первому предприятию...")
        first_business = found_businesses[0]
        
        # Поиск кликабельного элемента внутри
        click_selectors = [
            ".//span[contains(@class, 'search-business-snippet-view__title')]",
            ".//a[contains(@class, 'search-snippet-view__title')]",
            ".//div[contains(@class, 'search-snippet-view__title')]"
        ]
        
        clicked = False
        for click_selector in click_selectors:
            try:
                clickable = first_business.find_element(By.XPATH, click_selector)
                if clickable.is_displayed():
                    print(f"🖱️ Клик по элементу: {click_selector}")
                    clickable.click()
                    clicked = True
                    break
            except Exception as e:
                print(f"❌ Не удалось кликнуть: {e}")
        
        if not clicked:
            print("🖱️ Пробуем кликнуть по самому элементу...")
            try:
                first_business.click()
                clicked = True
            except Exception as e:
                print(f"❌ Клик не удался: {e}")
        
        if clicked:
            print("✅ Клик выполнен! Ожидание загрузки карточки...")
            time.sleep(5)
            
            # Проверка открытия карточки
            card_selectors = [
                "//div[contains(@class, 'business-card-view__main-wrapper')]",
                "//h1[contains(@class, 'card-title-view__title')]"
            ]
            
            card_opened = False
            for card_selector in card_selectors:
                try:
                    card_element = driver.find_element(By.XPATH, card_selector)
                    if card_element.is_displayed():
                        print(f"✅ Карточка открылась! Найден элемент: {card_selector}")
                        
                        # Попытка извлечь название
                        try:
                            title_element = driver.find_element(By.XPATH, "//h1[contains(@class, 'card-title-view__title')]")
                            title = title_element.text.strip()
                            print(f"📋 Название: {title}")
                        except:
                            print("📋 Название не найдено")
                        
                        # Попытка извлечь адрес
                        try:
                            address_element = driver.find_element(By.XPATH, "//div[contains(@class, 'business-contacts-view__address-link')]")
                            address = address_element.text.strip()
                            print(f"📍 Адрес: {address}")
                        except:
                            print("📍 Адрес не найден")
                        
                        card_opened = True
                        break
                except:
                    continue
            
            if not card_opened:
                print("❌ Карточка не открылась или не найдена")
        
        print("\n👀 Браузер оставлен открытым для анализа")
        print("Нажмите Enter для закрытия...")
        input()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        browser_manager.close()

if __name__ == "__main__":
    simple_click_test()
