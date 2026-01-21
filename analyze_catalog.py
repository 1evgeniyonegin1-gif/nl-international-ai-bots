#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для анализа полного каталога NL International
Извлекает информацию о продуктах из 120 текстовых файлов
"""

import os
import re
from pathlib import Path
from typing import List, Dict
import json

# Путь к папке с каталогом
CATALOG_DIR = r"c:\Users\mafio\OneDrive\Документы\projects\nl-international-ai-bots\полный каталог"
KNOWLEDGE_BASE_DIR = r"c:\Users\mafio\OneDrive\Документы\projects\nl-international-ai-bots\content\knowledge_base\products"

def read_catalog_file(file_path: str) -> str:
    """Читает содержимое файла каталога"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Ошибка чтения {file_path}: {e}")
        return ""

def extract_product_info(text: str, page_num: int) -> List[Dict]:
    """
    Извлекает информацию о продуктах из текста страницы
    """
    products = []

    # Паттерны для поиска названий продуктов
    # Основные продуктовые линейки
    product_patterns = [
        # ED Smart коктейли
        (r'ED Smart\s*(\d+\.\d+)?', 'ED Smart'),
        (r'Energy Diet\s*HD', 'Energy Diet HD'),

        # Чаи
        (r'Enerwood\s+Classic', 'Enerwood Classic'),
        (r'(Black|Green|Red|White|MIX)\s+Tea', 'Tea'),
        (r'Herbal Tea', 'Herbal Tea'),

        # Программы похудения
        (r'3D\s*SLIM\s+Program', '3D SLIM Program'),
        (r'DrainEffect\s+(Green|Red)', 'DrainEffect'),
        (r'White\s+Tea\s+SlimDose', 'White Tea SlimDose'),
        (r'3D\s*SLIM\s+cosmetics', '3D SLIM cosmetics'),

        # Адаптогены
        (r'BioDrone', 'BioDrone'),
        (r'BioSetting', 'BioSetting'),
        (r'BioTuning', 'BioTuning'),
        (r'PH\s+Balance\s+Stones', 'PH Balance Stones'),

        # БАДы
        (r'Pro-indole', 'Pro-indole'),
        (r'Beauty\s+blend', 'Beauty blend'),
        (r'Be\s+Best', 'Be Best'),
        (r'Metabiotic', 'Metabiotic'),
        (r'Lactoferra', 'Lactoferra'),
        (r'Detox\s+Step\s+[1-3]\s+PLUS', 'Detox Step'),
        (r'Soft\s+Sorb', 'Soft Sorb'),
        (r'Gelm\s+Cleanse', 'Gelm Cleanse'),

        # Коллаген
        (r'Collagentrinity', 'Collagentrinity'),
        (r'Collagen\s+Peptides', 'Collagen Peptides'),
        (r'Marine\s+Collagen', 'Marine Collagen'),

        # Greenflash
        (r'Greenflash', 'Greenflash'),
        (r'5-НТР\s+liposomal', '5-HTP liposomal'),
        (r'Metabrain\s+liposomal', 'Metabrain liposomal'),
        (r'Neuromedium\s+liposomal', 'Neuromedium liposomal'),
        (r'Vitamin\s+C\s+liposomal', 'Vitamin C liposomal'),

        # Key to health
        (r'Key\s+to\s+health', 'Key to health'),

        # Детские продукты
        (r'PROHELPER', 'PROHELPER'),
        (r'Omega-3\s+DHA\s+&\s+Mg\+B6\s+for\s+kids', 'Omega-3 DHA & Mg+B6 for kids'),
        (r'Baby\s+Cosmetics', 'Baby Cosmetics'),
        (r'Kids\s+Cosmetics', 'Kids Cosmetics'),

        # Для животных
        (r'NL\s+Pets', 'NL Pets'),

        # Косметика
        (r'Biome', 'Biome'),
        (r'Be\s+Loved\s+Oriental', 'Be Loved Oriental'),
        (r'Be\s+Loved\s+Body', 'Be Loved Body'),
        (r'Be\s+Loved\s+Sun', 'Be Loved Sun'),
        (r'Occuba', 'Occuba'),
        (r'The\s+LAB', 'The LAB'),
        (r'Sklaer', 'Sklaer'),
        (r'Smartum\s+Max', 'Smartum Max'),

        # Домашние товары
        (r'Fineffect\s+Textile', 'Fineffect Textile'),
    ]

    # Поиск продуктов в тексте
    for pattern, category in product_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            product_name = match.group(0)

            # Извлекаем контекст вокруг названия (следующие 500 символов)
            start_pos = match.start()
            context = text[start_pos:start_pos + 500]

            # Пытаемся найти описание, состав, объем
            description = extract_description(context)
            composition = extract_composition(context)
            volume = extract_volume(context)

            products.append({
                'name': product_name.strip(),
                'category': category,
                'page': page_num,
                'description': description,
                'composition': composition,
                'volume': volume,
                'context': context[:200]  # Первые 200 символов контекста
            })

    return products

def extract_description(text: str) -> str:
    """Извлекает описание продукта"""
    # Ищем текст до первого маркера (•, -, RU, KZ)
    match = re.search(r'([А-Яа-яёЁA-Za-z\s,\.]+?)(?:•|—|RU|KZ|\n\n)', text)
    if match:
        desc = match.group(1).strip()
        if len(desc) > 10 and len(desc) < 200:
            return desc
    return ""

def extract_composition(text: str) -> str:
    """Извлекает состав продукта"""
    # Ищем маркеры состава
    comp_match = re.search(r'•\s*([^•\n]{20,300})', text)
    if comp_match:
        return comp_match.group(1).strip()
    return ""

def extract_volume(text: str) -> str:
    """Извлекает объем/количество"""
    # Ищем упоминания саше, капсул, таблеток, мл, г
    volume_patterns = [
        r'(\d+\s*(?:саше|монодоз[аы]?|капсул[аы]?|таблет[оки]{2,3}|мл|г|пакет[ов]{0,2}))',
        r'(\d+\s*x\s*\d+\s*(?:мл|г))',
    ]

    for pattern in volume_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""

def analyze_catalog():
    """Основная функция анализа каталога"""
    all_products = []

    # Читаем все файлы pdf2text_page_*.txt
    catalog_path = Path(CATALOG_DIR)
    files = sorted(catalog_path.glob("pdf2text_page_*.txt"))

    print(f"Найдено файлов: {len(files)}")

    for file in files:
        # Извлекаем номер страницы
        match = re.search(r'page_(\d+)', file.name)
        if match:
            page_num = int(match.group(1))
        else:
            page_num = 0

        # Читаем файл
        content = read_catalog_file(str(file))

        if content:
            # Извлекаем информацию о продуктах
            products = extract_product_info(content, page_num)
            all_products.extend(products)

            if products:
                print(f"Страница {page_num}: найдено {len(products)} продуктов")

    print(f"\nВсего найдено продуктов: {len(all_products)}")

    # Удаляем дубликаты по названию
    unique_products = {}
    for p in all_products:
        name = p['name']
        if name not in unique_products:
            unique_products[name] = p
        else:
            # Объединяем информацию
            if not unique_products[name]['description'] and p['description']:
                unique_products[name]['description'] = p['description']
            if not unique_products[name]['composition'] and p['composition']:
                unique_products[name]['composition'] = p['composition']
            if not unique_products[name]['volume'] and p['volume']:
                unique_products[name]['volume'] = p['volume']

    print(f"Уникальных продуктов: {len(unique_products)}")

    # Сохраняем в JSON
    output_file = os.path.join(os.path.dirname(CATALOG_DIR), 'catalog_products.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(list(unique_products.values()), f, ensure_ascii=False, indent=2)

    print(f"\nРезультаты сохранены в: {output_file}")

    return list(unique_products.values())

def analyze_knowledge_base():
    """Анализирует существующие продукты в базе знаний"""
    kb_path = Path(KNOWLEDGE_BASE_DIR)
    if not kb_path.exists():
        print(f"Папка базы знаний не найдена: {KNOWLEDGE_BASE_DIR}")
        return []

    kb_products = []
    for file in kb_path.glob("*.txt"):
        kb_products.append(file.stem)

    print(f"\nВ базе знаний найдено продуктов: {len(kb_products)}")
    return kb_products

def compare_catalogs(catalog_products, kb_products):
    """Сравнивает каталог с базой знаний"""
    catalog_names = set(p['name'] for p in catalog_products)
    kb_names = set(kb_products)

    # Продукты, которых нет в базе знаний
    missing_in_kb = catalog_names - kb_names

    # Продукты, которых нет в каталоге
    missing_in_catalog = kb_names - catalog_names

    print(f"\n=== СРАВНЕНИЕ ===")
    print(f"Продуктов в каталоге: {len(catalog_names)}")
    print(f"Продуктов в базе знаний: {len(kb_names)}")
    print(f"Отсутствует в базе знаний: {len(missing_in_kb)}")
    print(f"Отсутствует в каталоге: {len(missing_in_catalog)}")

    if missing_in_kb:
        print("\nОтсутствуют в базе знаний:")
        for name in sorted(missing_in_kb):
            print(f"  - {name}")

    return {
        'missing_in_kb': list(missing_in_kb),
        'missing_in_catalog': list(missing_in_catalog)
    }

if __name__ == "__main__":
    print("Анализ каталога NL International...")
    print("=" * 60)

    # Анализируем каталог
    catalog_products = analyze_catalog()

    # Анализируем базу знаний
    kb_products = analyze_knowledge_base()

    # Сравниваем
    comparison = compare_catalogs(catalog_products, kb_products)

    print("\nГотово!")
