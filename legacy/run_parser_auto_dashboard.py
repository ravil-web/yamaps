#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Автоматический запуск парсера с созданием современного дашборда
Дашборд создается автоматически после каждого парсинга в папке результатов
"""

from final_working_parser import FinalWorkingParser
import sys

def main():
    """Основная функция"""
    print("🚀 Автоматический парсер с дашбордом")
    print("=" * 50)
    
    # URL для парсинга (можно изменить)
    default_url = "https://yandex.ru/maps/39/rostov-na-donu/search/стоматология/?ll=39.806284%2C47.275656&z=12"
    
    # Получаем URL от пользователя или используем по умолчанию
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        print(f"🔗 Используется URL по умолчанию: {default_url}")
        print("💡 Для использования другого URL: python run_parser_auto_dashboard.py 'ваш_url'")
        url = default_url
    
    # Получаем количество предприятий
    try:
        if len(sys.argv) > 2:
            target_count = int(sys.argv[2])
        else:
            target_count = int(input("🎯 Введите количество предприятий для парсинга (по умолчанию 3): ") or "3")
    except ValueError:
        target_count = 3
        print("⚠️ Используется значение по умолчанию: 3 предприятия")
    
    print(f"\n📊 Параметры парсинга:")
    print(f"   🔗 URL: {url}")
    print(f"   🎯 Цель: {target_count} предприятий")
    print(f"   📁 Результаты: папка output/")
    print(f"   🌐 Дашборд: папка dashboard/ (в корне проекта)")
    print("=" * 50)
    
    # Создаем парсер
    parser = FinalWorkingParser(target_count=target_count)
    
    try:
        # Запускаем парсинг
        if parser.parse(url):
            print("\n✅ Парсинг завершен успешно!")
            
            # Сохраняем результаты (дашборд создается автоматически)
            parser.save_results()
            
            print("\n🎉 ВСЕ ГОТОВО!")
            print("📁 Проверьте папки:")
            print("   📄 output/ - JSON и Excel файлы")
            print("   🌐 dashboard/ - HTML дашборд (в корне проекта)")
            print("\n💡 Дашборд создан автоматически и готов к просмотру!")
            
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
