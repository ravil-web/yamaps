#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Анализ логов парсинга для выявления медленных участков
"""

import os
import re
from datetime import datetime

def analyze_parsing_logs():
    """Анализ логов парсинга"""
    
    # Ищем последние лог файлы
    log_dirs = ['parsing_results/*/logs', 'parsing_results/logs', 'logs']
    log_files = []
    
    for log_dir in log_dirs:
        if '*' in log_dir:
            # Поиск в папках сессий
            base_dir = log_dir.split('*')[0]
            if os.path.exists(base_dir):
                for session_folder in os.listdir(base_dir):
                    session_path = os.path.join(base_dir, session_folder)
                    if os.path.isdir(session_path):
                        logs_path = os.path.join(session_path, 'logs')
                        if os.path.exists(logs_path):
                            for file in os.listdir(logs_path):
                                if file.endswith('.log'):
                                    log_files.append(os.path.join(logs_path, file))
        else:
            if os.path.exists(log_dir):
                for file in os.listdir(log_dir):
                    if file.endswith('.log'):
                        log_files.append(os.path.join(log_dir, file))
    
    if not log_files:
        print("❌ Лог файлы не найдены")
        return
    
    # Берем самый новый лог файл
    latest_log = max(log_files, key=os.path.getmtime)
    print(f"📄 Анализируем лог: {latest_log}")
    
    analyze_log_file(latest_log)

def analyze_log_file(log_path):
    """Анализ конкретного лог файла"""
    
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"\n📊 СТАТИСТИКА ЛОГА:")
    print(f"   Всего строк: {len(lines)}")
    
    # Поиск этапов парсинга предприятий
    business_times = []
    product_parsing_times = []
    
    current_business = None
    current_business_start = None
    
    for line in lines:
        # Начало предприятия
        if "ПРЕДПРИЯТИЕ" in line and "/" in line:
            match = re.search(r'ПРЕДПРИЯТИЕ (\d+)/(\d+)', line)
            if match:
                if current_business_start:
                    # Завершаем предыдущее предприятие
                    pass
                current_business = int(match.group(1))
                current_business_start = extract_timestamp(line)
        
        # Завершение предприятия
        elif "УСПЕШНО за" in line or "НЕ УДАЛОСЬ за" in line:
            match = re.search(r'за ([\d.]+)с', line)
            if match and current_business:
                time_taken = float(match.group(1))
                business_times.append({
                    'business_number': current_business,
                    'time': time_taken,
                    'status': 'success' if 'УСПЕШНО' in line else 'failed'
                })
        
        # Товары и услуги
        elif "Товары и услуги - ЗАВЕРШЕН за" in line:
            match = re.search(r'за ([\d.]+)с', line)
            if match and current_business:
                time_taken = float(match.group(1))
                product_parsing_times.append({
                    'business_number': current_business,
                    'time': time_taken
                })
        
        # Количество найденных товаров
        elif "Найдено товаров:" in line:
            match = re.search(r'Найдено товаров: (\d+)', line)
            if match and current_business:
                count = int(match.group(1))
                # Обновляем информацию о товарах
                for item in product_parsing_times:
                    if item['business_number'] == current_business and 'product_count' not in item:
                        item['product_count'] = count
                        break
    
    # Анализ времени по предприятиям
    if business_times:
        print(f"\n⏱️ ВРЕМЯ ПАРСИНГА ПРЕДПРИЯТИЙ:")
        for bt in business_times:
            status_emoji = "✅" if bt['status'] == 'success' else "❌"
            print(f"   {status_emoji} Предприятие {bt['business_number']}: {bt['time']:.1f}с")
        
        avg_time = sum(bt['time'] for bt in business_times) / len(business_times)
        max_time = max(bt['time'] for bt in business_times)
        min_time = min(bt['time'] for bt in business_times)
        
        print(f"\n📈 СТАТИСТИКА ВРЕМЕНИ:")
        print(f"   Среднее: {avg_time:.1f}с")
        print(f"   Максимум: {max_time:.1f}с")
        print(f"   Минимум: {min_time:.1f}с")
        
        # Выявляем медленные предприятия
        slow_threshold = avg_time * 2
        slow_businesses = [bt for bt in business_times if bt['time'] > slow_threshold]
        
        if slow_businesses:
            print(f"\n🐌 МЕДЛЕННЫЕ ПРЕДПРИЯТИЯ (>{slow_threshold:.1f}с):")
            for bt in slow_businesses:
                print(f"   ⚠️ Предприятие {bt['business_number']}: {bt['time']:.1f}с")
    
    # Анализ времени парсинга товаров
    if product_parsing_times:
        print(f"\n🛍️ ВРЕМЯ ПАРСИНГА ТОВАРОВ:")
        for pt in product_parsing_times:
            count = pt.get('product_count', '?')
            time_per_item = pt['time'] / pt.get('product_count', 1) if pt.get('product_count') else 0
            print(f"   Предприятие {pt['business_number']}: {pt['time']:.1f}с ({count} товаров, {time_per_item:.2f}с/товар)")
        
        # Выявляем медленный парсинг товаров
        slow_product_parsing = [pt for pt in product_parsing_times if pt['time'] > 30]
        if slow_product_parsing:
            print(f"\n🐌 МЕДЛЕННЫЙ ПАРСИНГ ТОВАРОВ (>30с):")
            for pt in slow_product_parsing:
                count = pt.get('product_count', '?')
                print(f"   ⚠️ Предприятие {pt['business_number']}: {pt['time']:.1f}с для {count} товаров")
    
    # Поиск ошибок
    errors = [line for line in lines if "ERROR" in line or "❌" in line]
    if errors:
        print(f"\n❌ НАЙДЕНО ОШИБОК: {len(errors)}")
        for error in errors[-5:]:  # Показываем последние 5 ошибок
            print(f"   {error.strip()}")

def extract_timestamp(line):
    """Извлечение временной метки из строки лога"""
    match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
    if match:
        return datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S,%f')
    return None

if __name__ == "__main__":
    print("🔍 АНАЛИЗ ЛОГОВ ПАРСИНГА")
    print("=" * 50)
    analyze_parsing_logs()
