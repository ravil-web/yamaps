#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест исправленного парсера - проверка кликов по разным предприятиям
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

class ClickTester:
    def __init__(self):
        self.driver = None
        self.clicked_businesses = []
    
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
    
    def get_business_elements(self):
        """Получение элементов предприятий по исправленным селекторам"""
        selectors = [
            "//div[contains(@class, 'search-business-snippet-view')]",
            "//a[contains(@href, '/org/')]",
            "//div[contains(@class, 'search-snippet-view')]"
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"✅ Найдено {len(elements)} элементов с селектором: {selector}")
                    # Фильтруем только видимые с текстом
                    valid_elements = []
                    for elem in elements:
                        try:
                            if elem.is_displayed() and elem.text.strip():
                                valid_elements.append(elem)
                        except:
                            continue
                    
                    if valid_elements:
                        print(f"✅ Из них {len(valid_elements)} валидных")
                        return valid_elements
            except:
                continue
        
        return []
    
    def click_business(self, element, index):
        """Клик по предприятию"""
        print(f"\n🎯 ПОПЫТКА КЛИКА НА ПРЕДПРИЯТИЕ {index + 1}")
        
        try:
            # Получаем название для отладки
            try:
                title_elem = element.find_element(By.XPATH, ".//div[contains(@class, 'search-business-snippet-view__title')]")
                business_name = title_elem.text.strip()
                print(f"   Название: {business_name}")
            except:
                business_name = f"Предприятие {index + 1}"
                print(f"   Название не найдено, используем: {business_name}")
            
            # Прокрутка к элементу
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            
            # Сохраняем текущий URL
            current_url = self.driver.current_url
            print(f"   Текущий URL: {current_url}")
            
            # Пробуем клик по названию
            clickable_selectors = [
                ".//div[contains(@class, 'search-business-snippet-view__title')]",
                ".//a[contains(@href, '/org/')]"
            ]
            
            clicked = False
            for selector in clickable_selectors:
                try:
                    clickable = element.find_element(By.XPATH, selector)
                    if clickable.is_displayed():
                        print(f"   Кликаем по: {selector}")
                        clickable.click()
                        time.sleep(3)
                        
                        # Проверяем изменение URL
                        new_url = self.driver.current_url
                        if new_url != current_url:
                            print(f"   ✅ УСПЕХ! URL изменился")
                            print(f"   Новый URL: {new_url}")
                            self.clicked_businesses.append({
                                'index': index + 1,
                                'name': business_name,
                                'url': new_url
                            })
                            clicked = True
                            break
                        else:
                            print(f"   ❌ URL не изменился")
                except Exception as e:
                    print(f"   ❌ Ошибка клика по {selector}: {e}")
            
            if not clicked:
                print(f"   ❌ НЕ УДАЛОСЬ КЛИКНУТЬ")
                return False
            
            return True
            
        except Exception as e:
            print(f"   ❌ Общая ошибка клика: {e}")
            return False
    
    def return_to_list(self):
        """Возврат к списку"""
        print("   🔙 Возврат к списку...")
        
        try:
            # ESC
            self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(2)
            
            # Проверяем, что вернулись
            elements = self.get_business_elements()
            if elements:
                print("   ✅ Успешно вернулись к списку")
                return True
        except:
            pass
        
        try:
            # Кнопка назад
            self.driver.back()
            time.sleep(3)
            
            elements = self.get_business_elements()
            if elements:
                print("   ✅ Вернулись через кнопку назад")
                return True
        except:
            pass
        
        print("   ❌ Не удалось вернуться к списку")
        return False
    
    def test_multiple_clicks(self, url, count=5):
        """Тестирование кликов по нескольким предприятиям"""
        print("🚀 ТЕСТ КЛИКОВ ПО РАЗНЫМ ПРЕДПРИЯТИЯМ")
        print("=" * 50)
        
        self.driver.get(url)
        time.sleep(5)
        
        # Проверяем капчу
        if "SmartCaptcha" in self.driver.page_source:
            input("Решите капчу и нажмите Enter...")
            time.sleep(3)
        
        for attempt in range(count):
            print(f"\n📍 ПОПЫТКА {attempt + 1}/{count}")
            
            # Получаем элементы
            elements = self.get_business_elements()
            if not elements:
                print("❌ Не найдены элементы предприятий")
                break
            
            if attempt >= len(elements):
                print(f"❌ Недостаточно элементов. Найдено: {len(elements)}, нужен индекс: {attempt}")
                break
            
            # Кликаем по элементу с индексом attempt
            if self.click_business(elements[attempt], attempt):
                # Возвращаемся к списку
                if not self.return_to_list():
                    print("❌ Не удалось вернуться к списку")
                    break
            else:
                print(f"❌ Не удалось кликнуть на предприятие {attempt + 1}")
            
            time.sleep(2)
        
        # Результаты
        print(f"\n📈 РЕЗУЛЬТАТЫ ТЕСТА:")
        print(f"   Успешно обработано: {len(self.clicked_businesses)}/{count}")
        
        for business in self.clicked_businesses:
            print(f"   {business['index']}. {business['name']}")
        
        if len(self.clicked_businesses) == count:
            print("✅ ТЕСТ ПРОЙДЕН - кликаем по разным предприятиям!")
        else:
            print("❌ ТЕСТ НЕ ПРОЙДЕН - проблема остается")
        
        input("\nНажмите Enter для закрытия браузера...")
        self.driver.quit()

def main():
    url = "https://yandex.ru/maps/39/rostov-na-donu/search/Ростов%20на%20дону%20суворовский%20стоматология/?ll=39.806284%2C47.275656&sctx=ZAAAAAgCEAAaKAoSCbnEkQci10NAESl4CrlSn0dAEhIJ98ySADW1zj8R1lJA2v8Aqz8iBgABAgMEBSgKOABA0YgGSAFqAnJ1nQHNzMw9oAEAqAEAvQHFGEBwwgElzKy6tfoGxpeW5AXL5fTcA9Ka8PoDwpzMogT4sL%2FgA%2Fyw57rlBoICStCg0L7RgdGC0L7QsiDQvdCwINC00L7QvdGDINGB0YPQstC%2B0YDQvtCy0YHQutC40Lkg0YHRgtC%2B0LzQsNGC0L7Qu9C%2B0LPQuNGPigIAkgICMzmaAgxkZXNrdG9wLW1hcHPaAigKEgnfWbvtQuFDQBGw%2Fs8gd6FHQBISCYBnXaPlQN0%2FEQA8uDtrt7k%2F4AIB&sll=39.806284%2C47.275656&sspn=0.914172%2C0.200856&z=10.61"
    
    tester = ClickTester()
    tester.setup_driver()
    tester.test_multiple_clicks(url, count=5)

if __name__ == "__main__":
    main()
