#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Запуск парсера с автоматическим созданием HTML дашборда
"""

import sys
import os
from final_working_parser import FinalWorkingParser
from html_dashboard_generator import HTMLDashboardGenerator

def main():
    """Основная функция"""
    print("🚀 Запуск парсера с автоматическим созданием дашборда")
    print("=" * 60)
    
    # URL для парсинга (можно изменить)
    url = "https://yandex.ru/maps/39/rostov-na-donu/search/Ростов%20на%20дону%20суворовский%20стоматология/?ll=39.806284%2C47.275656&sctx=ZAAAAAgCEAAaKAoSCbnEkQci10NAESl4CrlSn0dAEhIJ98ySADW1zj8R1lJA2v8Aqz8iBgABAgMEBSgKOABA0YgGSAFqAnJ1nQHNzMw9oAEAqAEAvQHFGEBwwgElzKy6tfoGxpeW5AXL5fTcA9Ka8PoDwpzMogT4sL%2FgA%2Fyw57rlBoICStCg0L7RgdGC0L7QsiDQvdCwINC00L7QvdGDINGB0YPQstC%2B0YDQvtCy0YHQutC40Lkg0YHRgtC%2B0LzQsNGC0L7Qu9C%2B0LPQuNGPigIAkgICMzmaAgxkZXNrdG9wLW1hcHPaAigKEgnfWbvtQuFDQBGw%2Fs8gd6FHQBISCYBnXaPlQN0%2FEQA8uDtrt7k%2F4AIB&sll=39.806284%2C47.275656&sspn=0.914172%2C0.200856&z=10.61"
    
    # Количество предприятий для парсинга
    target_count = 3
    
    # Создаем парсер
    parser = FinalWorkingParser(target_count=target_count)
    
    try:
        print(f"🎯 Цель: {target_count} предприятий")
        print(f"🔗 URL: {url}")
        print("=" * 60)
        
        # Запускаем парсинг
        if parser.parse(url):
            print("\n✅ Парсинг завершен успешно!")
            
            # Сохраняем результаты
            parser.save_results()
            
            print("\n🌐 ДАШБОРД СОЗДАН АВТОМАТИЧЕСКИ!")
            print("📁 Файлы сохранены в папке 'output/'")
            print("📊 HTML дашборд в папке 'dashboards/'")
            print("\n🚀 Откройте HTML файл в браузере для просмотра результатов")
            
        else:
            print("❌ Парсинг завершился с ошибками")
            
    except KeyboardInterrupt:
        print("\n⏹️ Парсинг остановлен пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        parser.close()

if __name__ == "__main__":
    main()
