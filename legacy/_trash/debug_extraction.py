#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Диагностика извлечения данных из карточек предприятий
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

class ExtractionDebugger:
    def __init__(self):
        self.driver = None
    
    def setup_driver(self):
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.implicitly_wait(5)
        return True
    
    def debug_page_content(self, url):
        """Диагностика содержимого страницы"""
        print(f"🔍 ДИАГНОСТИКА СТРАНИЦЫ: {url}")
        print("=" * 70)
        
        self.driver.get(url)
        time.sleep(5)
        
        # 1. Основная информация о странице
        print(f"📄 URL: {self.driver.current_url}")
        print(f"📄 Заголовок страницы: {self.driver.title}")
        
        # 2. Проверяем наличие основного контейнера
        containers = [
            "//div[contains(@class, 'business-card-view')]",
            "//div[contains(@class, 'card-title-view')]",
            "//main",
            "//body"
        ]
        
        print(f"\n🏗️ КОНТЕЙНЕРЫ:")
        for container in containers:
            try:
                elem = self.driver.find_element(By.XPATH, container)
                print(f"   ✅ {container}: найден")
            except:
                print(f"   ❌ {container}: не найден")
        
        # 3. Тестируем селекторы названий
        name_selectors = [
            "//h1[contains(@class, 'card-title-view__title')]//a",
            "//h1[contains(@class, 'card-title-view__title')]",
            "//h1",
            "//title",
            "//*[@itemprop='name']",
            "//span[contains(@class, 'card-title')]",
            "//div[contains(@class, 'card-title')]"
        ]
        
        print(f"\n📛 ТЕСТИРОВАНИЕ СЕЛЕКТОРОВ НАЗВАНИЙ:")
        for selector in name_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    for i, elem in enumerate(elements[:3]):  # Показываем первые 3
                        try:
                            text = elem.text.strip() if elem.text else ""
                            if text:
                                print(f"   ✅ {selector} [{i}]: '{text}'")
                            else:
                                print(f"   ⚠️ {selector} [{i}]: элемент найден, но пустой")
                        except Exception as e:
                            print(f"   ❌ {selector} [{i}]: ошибка получения текста: {e}")
                else:
                    print(f"   ❌ {selector}: элементы не найдены")
            except Exception as e:
                print(f"   ❌ {selector}: ошибка поиска: {e}")
        
        # 4. Ищем любые заголовки
        print(f"\n🔍 ПОИСК ВСЕХ ЗАГОЛОВКОВ:")
        header_tags = ['h1', 'h2', 'h3', 'title']
        for tag in header_tags:
            try:
                elements = self.driver.find_elements(By.TAG_NAME, tag)
                if elements:
                    for i, elem in enumerate(elements[:3]):
                        try:
                            text = elem.text.strip() if elem.text else ""
                            if text and len(text) < 100:  # Разумная длина заголовка
                                print(f"   ✅ {tag.upper()} [{i}]: '{text}'")
                        except:
                            pass
            except:
                pass
        
        # 5. Ищем элементы с именами классов, содержащими "title" или "name"
        print(f"\n🏷️ ПОИСК ПО КЛАССАМ:")
        class_patterns = ['title', 'name', 'header', 'heading']
        for pattern in class_patterns:
            try:
                elements = self.driver.find_elements(By.XPATH, f"//*[contains(@class, '{pattern}')]")
                count = 0
                for elem in elements:
                    try:
                        text = elem.text.strip() if elem.text else ""
                        if text and len(text) < 100:
                            print(f"   ✅ Класс '{pattern}': '{text}'")
                            count += 1
                            if count >= 3:  # Ограничиваем вывод
                                break
                    except:
                        pass
                if count == 0:
                    print(f"   ❌ Класс '{pattern}': тексты не найдены")
            except:
                print(f"   ❌ Класс '{pattern}': ошибка поиска")
        
        # 6. Проверяем meta-теги
        print(f"\n📋 META-ТЕГИ:")
        meta_selectors = [
            "//meta[@property='og:title']",
            "//meta[@name='title']",
            "//meta[@itemprop='name']"
        ]
        for selector in meta_selectors:
            try:
                elem = self.driver.find_element(By.XPATH, selector)
                content = elem.get_attribute('content')
                if content:
                    print(f"   ✅ {selector}: '{content}'")
                else:
                    print(f"   ⚠️ {selector}: найден, но пустой")
            except:
                print(f"   ❌ {selector}: не найден")
        
        # 7. Сохраняем HTML для анализа
        try:
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            print(f"\n💾 HTML страницы сохранен в debug_page.html")
        except Exception as e:
            print(f"\n❌ Ошибка сохранения HTML: {e}")
        
        print("\n" + "=" * 70)
    
    def test_multiple_urls(self):
        """Тестирование нескольких URL'ов"""
        urls = [
            "https://yandex.ru/maps/org/estetika/164194457137/",
            "https://yandex.ru/maps/org/dentalkea/131230205132/",
            "https://yandex.ru/maps/org/milan/1078009594/"
        ]
        
        print("🚀 ТЕСТИРОВАНИЕ ИЗВЛЕЧЕНИЯ ДАННЫХ")
        print("=" * 70)
        
        for i, url in enumerate(urls):
            print(f"\n📍 ПРЕДПРИЯТИЕ {i+1}/3")
            self.debug_page_content(url)
            
            if i < len(urls) - 1:
                print("\n⏱️ Пауза 3 секунды...")
                time.sleep(3)
        
        print("\n🔚 ДИАГНОСТИКА ЗАВЕРШЕНА")
        input("Нажмите Enter для закрытия браузера...")
        self.driver.quit()

def main():
    debugger = ExtractionDebugger()
    debugger.setup_driver()
    debugger.test_multiple_urls()

if __name__ == "__main__":
    main()
