#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Отладочный скрипт для диагностики проблемы с кликами
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

class ClickDebugger:
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
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.driver.implicitly_wait(10)
        return True
    
    def debug_page_structure(self, url):
        print("🔍 ДИАГНОСТИКА СТРУКТУРЫ СТРАНИЦЫ")
        print("=" * 50)
        
        self.driver.get(url)
        time.sleep(5)
        
        # Проверяем капчу
        if "SmartCaptcha" in self.driver.page_source:
            input("Решите капчу и нажмите Enter...")
            time.sleep(3)
        
        # 1. Ищем все возможные селекторы для элементов списка
        selectors_to_test = [
            "//div[contains(@class, 'search-business-snippet-view')]",
            "//div[contains(@class, 'search-snippet-view')]", 
            "//li[contains(@class, 'serp-item')]",
            "//div[contains(@class, 'search-list-view')]//div",
            "//div[contains(@class, 'companies-list')]//div",
            "//a[contains(@href, '/org/')]",
            "//span[contains(@class, 'search-business-snippet-view__title')]",
            "//div[contains(@class, 'search-business-snippet-view__title')]"
        ]
        
        print("\n📋 ПОИСК ЭЛЕМЕНТОВ СПИСКА:")
        working_selector = None
        max_elements = 0
        
        for selector in selectors_to_test:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                print(f"   {selector}: {len(elements)} элементов")
                if len(elements) > max_elements:
                    max_elements = len(elements)
                    working_selector = selector
            except Exception as e:
                print(f"   {selector}: ОШИБКА - {e}")
        
        print(f"\n✅ Лучший селектор: {working_selector} ({max_elements} элементов)")
        
        if not working_selector:
            print("❌ Не найдено элементов списка!")
            return
        
        # 2. Анализируем первые 3 элемента
        elements = self.driver.find_elements(By.XPATH, working_selector)[:5]
        
        print(f"\n🔍 АНАЛИЗ ПЕРВЫХ {len(elements)} ЭЛЕМЕНТОВ:")
        for i, element in enumerate(elements):
            print(f"\n--- ЭЛЕМЕНТ {i+1} ---")
            try:
                # Получаем текст
                text = element.text.strip()[:100] if element.text else "НЕТ ТЕКСТА"
                print(f"   Текст: {text}")
                
                # Проверяем видимость
                is_displayed = element.is_displayed()
                print(f"   Видимый: {is_displayed}")
                
                # Получаем размеры
                size = element.size
                print(f"   Размер: {size}")
                
                # Получаем позицию
                location = element.location
                print(f"   Позиция: {location}")
                
                # Проверяем атрибуты
                class_name = element.get_attribute('class')
                print(f"   Классы: {class_name}")
                
                # Ищем кликабельные элементы внутри
                clickable_selectors = [
                    ".//span[contains(@class, 'search-business-snippet-view__title')]",
                    ".//div[contains(@class, 'search-business-snippet-view__title')]",
                    ".//a",
                    ".//h3",
                    ".//span[contains(@class, 'title')]"
                ]
                
                print("   Кликабельные элементы:")
                for cs in clickable_selectors:
                    try:
                        clickable = element.find_element(By.XPATH, cs)
                        if clickable.is_displayed():
                            print(f"     ✅ {cs}: '{clickable.text[:50] if clickable.text else 'НЕТ ТЕКСТА'}'")
                        else:
                            print(f"     ❌ {cs}: не видимый")
                    except:
                        print(f"     ❌ {cs}: не найден")
                
            except Exception as e:
                print(f"   ❌ Ошибка анализа: {e}")
        
        # 3. Тестируем клик
        print(f"\n🖱️ ТЕСТИРОВАНИЕ КЛИКОВ:")
        
        for i, element in enumerate(elements[:3]):  # Тестируем первые 3
            print(f"\n--- ТЕСТ КЛИКА НА ЭЛЕМЕНТ {i+1} ---")
            
            try:
                # Прокручиваем к элементу
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(1)
                
                # Пробуем разные способы клика
                click_methods = [
                    ("Прямой клик", lambda el: el.click()),
                    ("JavaScript клик", lambda el: self.driver.execute_script("arguments[0].click();", el)),
                    ("Клик на первый дочерний", lambda el: el.find_element(By.XPATH, ".//*[1]").click()),
                ]
                
                # Пробуем найти кликабельный элемент внутри
                clickable_found = False
                for cs in clickable_selectors:
                    try:
                        clickable = element.find_element(By.XPATH, cs)
                        if clickable.is_displayed():
                            print(f"   Пробуем клик на: {cs}")
                            
                            # Сохраняем текущий URL
                            current_url = self.driver.current_url
                            
                            # Кликаем
                            clickable.click()
                            time.sleep(3)
                            
                            # Проверяем изменение URL
                            new_url = self.driver.current_url
                            if new_url != current_url:
                                print(f"   ✅ УСПЕХ! URL изменился: {new_url}")
                                
                                # Возвращаемся назад
                                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                                time.sleep(2)
                                clickable_found = True
                                break
                            else:
                                print(f"   ❌ URL не изменился")
                    except Exception as e:
                        print(f"   ❌ Ошибка клика на {cs}: {e}")
                
                if not clickable_found:
                    print("   ❌ Ни один клик не сработал")
                    
            except Exception as e:
                print(f"   ❌ Общая ошибка клика: {e}")
        
        # 4. Проверяем, что происходит после возврата
        print(f"\n🔄 ПРОВЕРКА ПОСЛЕ ВОЗВРАТА:")
        time.sleep(2)
        
        new_elements = self.driver.find_elements(By.XPATH, working_selector)
        print(f"   Элементов до: {len(elements)}")
        print(f"   Элементов после: {len(new_elements)}")
        
        if len(new_elements) != len(elements):
            print("   ⚠️ КОЛИЧЕСТВО ЭЛЕМЕНТОВ ИЗМЕНИЛОСЬ!")
        else:
            print("   ✅ Количество элементов осталось прежним")
        
        # Сравниваем тексты
        for i in range(min(3, len(elements), len(new_elements))):
            old_text = elements[i].text[:50] if elements[i].text else "НЕТ"
            try:
                new_text = new_elements[i].text[:50] if new_elements[i].text else "НЕТ"
                if old_text == new_text:
                    print(f"   Элемент {i+1}: ✅ Текст тот же")
                else:
                    print(f"   Элемент {i+1}: ❌ Текст изменился")
                    print(f"     Был: {old_text}")
                    print(f"     Стал: {new_text}")
            except Exception as e:
                print(f"   Элемент {i+1}: ❌ Ошибка сравнения: {e}")
        
        print("\n" + "=" * 50)
        print("🔍 ДИАГНОСТИКА ЗАВЕРШЕНА")
        
        # Оставляем браузер открытым для ручного анализа
        input("\nНажмите Enter для закрытия браузера...")
        self.driver.quit()

def main():
    url = "https://yandex.ru/maps/39/rostov-na-donu/search/Ростов%20на%20дону%20суворовский%20стоматология/?ll=39.806284%2C47.275656&sctx=ZAAAAAgCEAAaKAoSCbnEkQci10NAESl4CrlSn0dAEhIJ98ySADW1zj8R1lJA2v8Aqz8iBgABAgMEBSgKOABA0YgGSAFqAnJ1nQHNzMw9oAEAqAEAvQHFGEBwwgElzKy6tfoGxpeW5AXL5fTcA9Ka8PoDwpzMogT4sL%2FgA%2Fyw57rlBoICStCg0L7RgdGC0L7QsiDQvdCwINC00L7QvdGDINGB0YPQstC%2B0YDQvtCy0YHQutC40Lkg0YHRgtC%2B0LzQsNGC0L7Qu9C%2B0LPQuNGPigIAkgICMzmaAgxkZXNrdG9wLW1hcHPaAigKEgnfWbvtQuFDQBGw%2Fs8gd6FHQBISCYBnXaPlQN0%2FEQA8uDtrt7k%2F4AIB&sll=39.806284%2C47.275656&sspn=0.914172%2C0.200856&z=10.61"
    
    debugger = ClickDebugger()
    debugger.setup_driver()
    debugger.debug_page_structure(url)

if __name__ == "__main__":
    main()
