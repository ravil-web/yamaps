#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тест улучшенной обработки списка предприятий
"""

from final_working_parser import FinalWorkingParser

def test_business_links():
    """Тестируем улучшенную обработку предприятий"""
    print("🧪 Тестирование улучшенной обработки предприятий")
    print("=" * 60)
    
    # Тестовый URL
    url = "https://yandex.ru/maps/39/rostov-na-donu/search/Ростов%20на%20дону%20суворовский%20стоматология/?ll=39.806284%2C47.275656&sctx=ZAAAAAgCEAAaKAoSCbnEkQci10NAESl4CrlSn0dAEhIJ98ySADW1zj8R1lJA2v8Aqz8iBgABAgMEBSgKOABA0YgGSAFqAnJ1nQHNzMw9oAEAqAEAvQHFGEBwwgElzKy6tfoGxpeW5AXL5fTcA9Ka8PoDwpzMogT4sL%2FgA%2Fyw57rlBoICStCg0L7RgdGC0L7QsiDQvdCwINC00L7QvdGDINGB0YPQstC%2B0YDQvtCy0YHQutC40Lkg0YHRgtC%2B0LzQsNGC0L7Qu9C%2B0LPQuNGPigIAkgICMzmaAgxkZXNrdG9wLW1hcHPaAigKEgnfWbvtQuFDQBGw%2Fs8gd6FHQBISCYBnXaPlQN0%2FEQA8uDtrt7k%2F4AIB&sll=39.806284%2C47.275656&sspn=0.914172%2C0.200856&z=10.61"
    
    parser = FinalWorkingParser(target_count=5)
    
    try:
        # Настраиваем браузер
        if not parser.setup_driver():
            print("❌ Не удалось запустить браузер")
            return
        
        # Переходим на страницу поиска
        if not parser.navigate_to_search(url):
            print("❌ Не удалось загрузить страницу поиска")
            return
        
        # Тестируем улучшенную функцию поиска ссылок
        print("\n🔍 Тестирование поиска ссылок на предприятия...")
        business_links = parser.get_business_links()
        
        if business_links:
            print(f"✅ Найдено {len(business_links)} ссылок на предприятия")
            print("\n📋 Первые 5 ссылок:")
            for i, link in enumerate(business_links[:5], 1):
                print(f"   {i}. {link}")
            
            # Тестируем переход к первому предприятию
            if business_links:
                print(f"\n🎯 Тестирование перехода к первому предприятию...")
                first_business = business_links[0]
                if parser.navigate_to_business(first_business):
                    print("✅ Успешно перешли к предприятию")
                    
                    # Тестируем извлечение данных
                    print("📊 Тестирование извлечения данных...")
                    business_data = parser.extract_business_data()
                    if business_data and business_data['name']:
                        print(f"✅ Данные извлечены: {business_data['name']}")
                        print(f"   📞 Телефонов: {len(business_data['phones'])}")
                        print(f"   🏷️ Категорий: {len(business_data['categories'])}")
                        print(f"   🛍️ Товаров: {len(business_data['products'])}")
                        print(f"   ⭐ Рейтинг: {business_data['rating']}")
                    else:
                        print("⚠️ Данные не извлечены")
                else:
                    print("❌ Не удалось перейти к предприятию")
        else:
            print("❌ Ссылки на предприятия не найдены")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
    finally:
        parser.close()

if __name__ == "__main__":
    test_business_links()
