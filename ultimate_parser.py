#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

def ultimate_parser():
    """Окончательный парсер - без лишних слов"""
    
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        # Модифицируем URL чтобы принудительно открыть список
        base_url = "https://yandex.ru/maps/39/rostov-na-donu/search/Ростов%20на%20дону%20суворовский%20стоматология/"
        
        # Добавляем параметр mode=list чтобы принудительно открыть список
        list_url = base_url + "?mode=list"
        
        print(f"🔗 Переход на: {list_url}")
        driver.get(list_url)
        time.sleep(10)
        
        # Если список не открылся, пробуем найти кнопку переключения
        print("🔍 Поиск кнопки списка...")
        
        # Возможные селекторы кнопки списка
        list_button_selectors = [
            "//button[contains(@aria-label, 'Список')]",
            "//button[contains(@title, 'Список')]", 
            "//button[contains(text(), 'Список')]",
            "//div[contains(@class, 'tabs')]//button[2]",
            "//button[contains(@class, 'list')]",
            "[data-bem*='list']",
            "[aria-label*='Список']"
        ]
        
        button_found = False
        for selector in list_button_selectors:
            try:
                if selector.startswith("//"):
                    buttons = driver.find_elements(By.XPATH, selector)
                else:
                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                
                if buttons:
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            print(f"✅ Найдена кнопка списка: {selector}")
                            driver.execute_script("arguments[0].click();", button)
                            time.sleep(5)
                            button_found = True
                            break
                    if button_found:
                        break
            except:
                continue
        
        if not button_found:
            print("⚠️ Кнопка списка не найдена, пробуем JavaScript...")
            # Принудительное переключение через JavaScript
            driver.execute_script("""
                // Ищем все кнопки и клики по тем, что могут переключить на список
                const buttons = document.querySelectorAll('button, [role="button"]');
                for (let btn of buttons) {
                    const text = btn.textContent || btn.getAttribute('aria-label') || btn.getAttribute('title') || '';
                    if (text.toLowerCase().includes('список') || text.toLowerCase().includes('list')) {
                        btn.click();
                        break;
                    }
                }
            """)
            time.sleep(5)
        
        # Сохраняем HTML после попытки переключения
        with open('ultimate_debug.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("💾 HTML сохранен в ultimate_debug.html")
        
        # Теперь ищем ЛЮБЫЕ ссылки на организации
        print("🔍 Поиск ссылок на организации...")
        
        # Массивная прокрутка для загрузки всего
        for i in range(20):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(1)
            
            # Прокрутка влево-вправо
            driver.execute_script("window.scrollBy(500, 0);")
            time.sleep(0.5)
            driver.execute_script("window.scrollBy(-500, 0);")
            time.sleep(0.5)
        
        # Поиск ВСЕХ ссылок с /org/
        all_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/org/')]")
        print(f"📊 Найдено ссылок с /org/: {len(all_links)}")
        
        # Извлекаем уникальные URL
        business_urls = []
        seen_urls = set()
        
        for link in all_links:
            try:
                href = link.get_attribute('href')
                if href and '/org/' in href and '/gallery/' not in href and '/reviews/' not in href:
                    clean_url = href.split('?')[0].split('#')[0]
                    if clean_url not in seen_urls:
                        seen_urls.add(clean_url)
                        business_urls.append(clean_url)
                        
                        # Пробуем получить название
                        try:
                            name = link.text.strip() or "Без названия"
                        except:
                            name = "Без названия"
                        
                        print(f"   ✅ {len(business_urls)}. {name}: {clean_url}")
                        
                        if len(business_urls) >= 50:  # Ограничиваем для теста
                            break
            except:
                continue
        
        # Если ссылок мало, пробуем кликать по элементам карты
        if len(business_urls) < 10:
            print("🔍 Мало ссылок, пробуем кликать по элементам карты...")
            
            # Ищем маркеры на карте
            markers = driver.find_elements(By.XPATH, "//div[contains(@class, 'placemark') or contains(@class, 'marker')]")
            print(f"📊 Найдено маркеров: {len(markers)}")
            
            for i, marker in enumerate(markers[:20]):  # Ограничиваем количество
                try:
                    print(f"🖱️ Клик по маркеру {i+1}")
                    driver.execute_script("arguments[0].click();", marker)
                    time.sleep(3)
                    
                    # Проверяем, появился ли новый URL
                    current_url = driver.current_url
                    if '/org/' in current_url and current_url not in seen_urls:
                        seen_urls.add(current_url)
                        business_urls.append(current_url)
                        print(f"   ✅ Получен URL: {current_url}")
                        
                        # Возвращаемся назад
                        driver.back()
                        time.sleep(2)
                        
                except Exception as e:
                    print(f"❌ Ошибка клика по маркеру {i+1}: {e}")
                    continue
        
        print(f"\n📊 ИТОГО найдено URL: {len(business_urls)}")
        
        # Сохраняем результаты
        with open('ultimate_results.json', 'w', encoding='utf-8') as f:
            json.dump(business_urls, f, ensure_ascii=False, indent=2)
        
        print("💾 Результаты сохранены в ultimate_results.json")
        
        return business_urls
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []
        
    finally:
        driver.quit()

if __name__ == "__main__":
    print("🚀 ЗАПУСК УЛЬТИМАТИВНОГО ПАРСЕРА")
    print("="*50)
    
    urls = ultimate_parser()
    
    if urls:
        print(f"✅ УСПЕХ! Найдено {len(urls)} предприятий")
        for i, url in enumerate(urls, 1):
            print(f"   {i}. {url}")
    else:
        print("❌ НЕУДАЧА! Предприятия не найдены")
