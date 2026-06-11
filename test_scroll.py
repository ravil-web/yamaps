#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from config import *

def test_scroll_and_find():
    """Тест прокрутки и поиска предприятий"""
    
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        print("🔍 Загружаем страницу...")
        driver.get(SEARCH_URL)
        time.sleep(5)
        
        print("\n" + "="*60)
        print("ТЕСТ ПРОКРУТКИ И ПОИСКА")
        print("="*60)
        
        # Начальное состояние
        print("\n📊 НАЧАЛЬНОЕ СОСТОЯНИЕ:")
        overlay_links = driver.find_elements(By.XPATH, "//a[contains(@class, 'link-overlay')]")
        print(f"   Ссылок link-overlay: {len(overlay_links)}")
        
        for i, link in enumerate(overlay_links, 1):
            href = link.get_attribute('href')
            print(f"   {i}. {href}")
        
        # Прокручиваем страницу пошагово
        print("\n📜 ПРОКРУТКА ПОШАГОВО:")
        
        for step in range(1, 21):  # 20 шагов прокрутки
            print(f"\n   Шаг {step}:")
            
            # Прокручиваем вниз
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2)
            
            # Проверяем количество ссылок
            current_overlay = driver.find_elements(By.XPATH, "//a[contains(@class, 'link-overlay')]")
            print(f"     Ссылок link-overlay: {len(current_overlay)}")
            
            # Если количество изменилось, показываем новые
            if len(current_overlay) > len(overlay_links):
                print(f"     🆕 НОВЫЕ ССЫЛКИ:")
                for i in range(len(overlay_links), len(current_overlay)):
                    href = current_overlay[i].get_attribute('href')
                    print(f"       {i+1}. {href}")
                overlay_links = current_overlay
            
            # Проверяем, есть ли кнопка "Показать еще"
            show_more = driver.find_elements(By.XPATH, "//button[contains(text(), 'Показать еще')]")
            if show_more:
                print(f"     🔘 Найдена кнопка 'Показать еще': {len(show_more)}")
                for btn in show_more:
                    if btn.is_displayed():
                        print(f"       - Видима: {btn.text}")
                        try:
                            btn.click()
                            print(f"       ✅ Кликнули по кнопке")
                            time.sleep(3)
                        except:
                            print(f"       ❌ Ошибка клика")
        
        # Финальное состояние
        print("\n📊 ФИНАЛЬНОЕ СОСТОЯНИЕ:")
        final_overlay = driver.find_elements(By.XPATH, "//a[contains(@class, 'link-overlay')]")
        print(f"   Всего ссылок link-overlay: {len(final_overlay)}")
        
        for i, link in enumerate(final_overlay, 1):
            href = link.get_attribute('href')
            print(f"   {i}. {href}")
        
        # Проверяем все ссылки с /org/
        print(f"\n🔗 ВСЕ ССЫЛКИ С /org/:")
        all_org = driver.find_elements(By.XPATH, "//a[contains(@href, '/org/')]")
        print(f"   Всего ссылок с /org/: {len(all_org)}")
        
        org_urls = []
        for link in all_org:
            href = link.get_attribute('href')
            if href and '/org/' in href:
                clean_url = href.split('/gallery/')[0].split('/reviews/')[0].split('/photos/')[0]
                if not clean_url.endswith('/'):
                    clean_url += '/'
                if clean_url not in org_urls:
                    org_urls.append(clean_url)
        
        print(f"   Уникальных организаций: {len(org_urls)}")
        for i, url in enumerate(org_urls, 1):
            print(f"   {i}. {url}")
        
        print("\n" + "="*60)
        print("ТЕСТ ЗАВЕРШЕН")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    test_scroll_and_find()
