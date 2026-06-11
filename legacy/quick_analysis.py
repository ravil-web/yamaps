#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import pandas as pd
from collections import Counter
import glob
from config import *

def quick_analysis():
    """Быстрый анализ данных парсинга"""
    print("📊 БЫСТРЫЙ АНАЛИЗ ДАННЫХ ПАРСИНГА")
    print("="*60)
    
    data_folder = FOLDER_STRUCTURE['base_folder']
    businesses_folder = f"{data_folder}/{FOLDER_STRUCTURE['businesses_subfolder']}"
    
    # Загружаем все данные
    all_businesses = []
    business_folders = glob.glob(f"{businesses_folder}/*/")
    
    print(f"🔍 Найдено папок с данными: {len(business_folders)}")
    
    for folder in business_folders:
        try:
            json_files = glob.glob(f"{folder}/*.json")
            for json_file in json_files:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['folder'] = os.path.basename(folder)
                    all_businesses.append(data)
        except Exception as e:
            print(f"❌ Ошибка загрузки {folder}: {e}")
    
    if not all_businesses:
        print("❌ Данные не найдены!")
        return
    
    print(f"✅ Загружено предприятий: {len(all_businesses)}")
    print()
    
    # Основная статистика
    print("📈 ОСНОВНАЯ СТАТИСТИКА:")
    print("-" * 30)
    
    # Рейтинги
    ratings = []
    for b in all_businesses:
        rating = b.get('rating')
        if rating is not None:
            try:
                # Пытаемся преобразовать в число
                if isinstance(rating, str):
                    # Убираем лишние символы и преобразуем в float
                    rating = float(rating.replace(',', '.').replace('⭐', '').strip())
                else:
                    rating = float(rating)
                ratings.append(rating)
            except (ValueError, TypeError):
                continue
    
    if ratings:
        print(f"📊 Средний рейтинг: {sum(ratings)/len(ratings):.2f}")
        print(f"📊 Максимальный рейтинг: {max(ratings)}")
        print(f"📊 Минимальный рейтинг: {min(ratings)}")
    else:
        print("📊 Рейтинги: не найдено")
    
    # Категории
    categories = []
    for business in all_businesses:
        cats = business.get('categories', [])
        if isinstance(cats, str):
            cats = [cats]
        categories.extend(cats)
    
    if categories:
        category_counts = Counter(categories)
        print(f"\n🏷️ Топ-5 категорий:")
        for i, (cat, count) in enumerate(category_counts.most_common(5), 1):
            print(f"   {i}. {cat}: {count} предприятий")
    
    # Товары и услуги
    total_products = sum(len(b.get('products_and_services', [])) for b in all_businesses)
    print(f"\n🛍️ Всего товаров/услуг: {total_products}")
    
    # Отзывы
    total_reviews = sum(len(b.get('reviews', [])) for b in all_businesses)
    print(f"💬 Всего отзывов: {total_reviews}")
    
    # Телефоны
    total_phones = sum(len(b.get('phones', [])) for b in all_businesses)
    print(f"📞 Всего телефонов: {total_phones}")
    
    # Сессии парсинга
    sessions = set(b.get('folder', '') for b in all_businesses)
    print(f"🔄 Сессий парсинга: {len(sessions)}")
    
    # Успешность парсинга
    successful = sum(1 for b in all_businesses if b.get('name') and b.get('address'))
    success_rate = (successful / len(all_businesses)) * 100
    print(f"✅ Успешность парсинга: {success_rate:.1f}%")
    
    print()
    print("🏆 ЛУЧШИЕ ПРЕДПРИЯТИЯ:")
    print("-" * 30)
    
    # Топ по рейтингу
    top_rated = sorted(all_businesses, key=lambda x: x.get('rating', 0), reverse=True)[:5]
    for i, business in enumerate(top_rated, 1):
        print(f"{i}. {business.get('name', 'Unknown')} - {business.get('rating', 0)}⭐")
    
    print()
    print("📋 ДЕТАЛЬНАЯ ИНФОРМАЦИЯ:")
    print("-" * 30)
    
    # Создаем DataFrame для анализа
    df = pd.DataFrame(all_businesses)
    
    if not df.empty:
        print(f"📊 Всего записей: {len(df)}")
        print(f"📊 Заполненных названий: {df['name'].notna().sum()}")
        print(f"📊 Заполненных адресов: {df['address'].notna().sum()}")
        print(f"📊 Заполненных рейтингов: {df['rating'].notna().sum()}")
        
        # Статистика по папкам
        if 'folder' in df.columns:
            print(f"\n📁 Статистика по папкам:")
            folder_stats = df['folder'].value_counts()
            for folder, count in folder_stats.items():
                print(f"   {folder}: {count} предприятий")
    
    print()
    print("🎯 РЕКОМЕНДАЦИИ:")
    print("-" * 30)
    
    if success_rate < 90:
        print("⚠️ Низкая успешность парсинга. Проверьте селекторы и логику извлечения данных.")
    
    if total_products == 0:
        print("⚠️ Товары/услуги не извлекаются. Проверьте логику парсинга товаров.")
    
    if total_reviews == 0:
        print("⚠️ Отзывы не извлекаются. Проверьте логику парсинга отзывов.")
    
    if len(sessions) == 1:
        print("ℹ️ Все данные из одной сессии. Рассмотрите запуск нескольких парсингов для сравнения.")
    
    print("✅ Анализ завершен!")

if __name__ == "__main__":
    quick_analysis()
