#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import glob
from config import *

def debug_products_structure():
    """Диагностика структуры данных о товарах"""
    data_folder = FOLDER_STRUCTURE['base_folder']
    businesses_folder = f"{data_folder}/{FOLDER_STRUCTURE['businesses_subfolder']}"
    
    print("🔍 Диагностика структуры данных о товарах...")
    print(f"📁 Папка с данными: {businesses_folder}")
    
    business_folders = glob.glob(f"{businesses_folder}/*/")
    print(f"📂 Найдено папок предприятий: {len(business_folders)}")
    
    total_businesses = 0
    total_products = 0
    businesses_with_products = 0
    
    for folder in business_folders:
        try:
            json_files = glob.glob(f"{folder}/*.json")
            for json_file in json_files:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    total_businesses += 1
                    
                    business_name = data.get('name', 'Unknown')
                    products = data.get('products_and_services', [])
                    
                    print(f"\n🏢 Предприятие: {business_name}")
                    print(f"   📦 Тип данных products_and_services: {type(products)}")
                    print(f"   📦 Количество элементов: {len(products)}")
                    
                    if products:
                        businesses_with_products += 1
                        total_products += len(products)
                        
                        print(f"   📋 Первые 3 товара:")
                        for i, product in enumerate(products[:3]):
                            print(f"      {i+1}. Тип: {type(product)}")
                            if isinstance(product, dict):
                                print(f"         Ключи: {list(product.keys())}")
                                print(f"         name: {product.get('name', 'N/A')}")
                                print(f"         price: {product.get('price', 'N/A')}")
                            else:
                                print(f"         Значение: {product}")
                    
                    if total_businesses >= 5:  # Показываем только первые 5 предприятий
                        break
                        
        except Exception as e:
            print(f"❌ Ошибка при чтении {folder}: {e}")
    
    print(f"\n📊 ИТОГИ:")
    print(f"   Всего предприятий: {total_businesses}")
    print(f"   Предприятий с товарами: {businesses_with_products}")
    print(f"   Всего товаров: {total_products}")

if __name__ == "__main__":
    debug_products_structure()
