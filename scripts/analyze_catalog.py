#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для анализа полного каталога NL International
Извлекает информацию о продуктах из 120 текстовых файлов
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Set

# Путь к проекту
PROJECT_ROOT = Path(r"c:\Users\mafio\OneDrive\Документы\projects\nl-international-ai-bots")
CATALOG_DIR = PROJECT_ROOT / "полный каталог"
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "content" / "knowledge_base" / "products"


class ProductExtractor:
    """Извлекает информацию о продуктах из текста каталога"""

    def __init__(self):
        self.products = []
        self.current_product = None

    def extract_price(self, text: str) -> tuple:
        """Извлекает цену и PV из текста"""
        # Паттерны для цены
        price_patterns = [
            r'(\d+\s*\d*)\s*₽',
            r'(\d+\s*\d*)\s*руб',
            r'(\d+\s*\d*)\s*тг',
            r'(\d+\s*\d*)\s*теңге',
        ]

        # Паттерны для PV
        pv_patterns = [
            r'(\d+)\s*PV',
            r'PV\s*(\d+)',
            r'(\d+)\s*балл',
        ]

        price = None
        pv = None

        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                price_str = match.group(1).replace(' ', '')
                try:
                    price = int(price_str)
                    break
                except ValueError:
                    pass

        for pattern in pv_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    pv = int(match.group(1))
                    break
                except ValueError:
                    pass

        return price, pv

    def is_product_title(self, line: str) -> bool:
        """Определяет, является ли строка названием продукта"""
        # Исключаем заголовки разделов
        section_keywords = [
            'Статья', 'Мақала', 'Содержание', 'Мазмұны',
            'Для детей', 'Балалар үшін', 'Для животных',
            'Уход', 'Күтім', 'Дом', 'Үй', 'Здоровье',
            'Денсаулық', 'Коктейли', 'Коктейльдер',
            'RU', 'KZ', 'Place of power', 'Место силы'
        ]

        for keyword in section_keywords:
            if keyword in line:
                return False

        # Проверяем, есть ли маркеры продукта
        product_markers = ['•', 'ED ', 'NL ', 'Bio', 'Pro-', 'Collagen',
                          'Green', 'Drain', 'Slim', 'Detox', 'Meta',
                          'Lacto', 'Be ', 'The LAB', 'Occuba', 'Sklaer',
                          'Smartum', 'PROHELPER', 'Omega-3', 'Baby',
                          'Kids', 'Pets', 'Biome', 'Enerwood', 'Herbal',
                          'Beauty', 'Key to', 'Soft', 'Gelm', 'White Tea',
                          'Fineffect', 'Oriental', 'Body', 'Sun']

        for marker in product_markers:
            if marker in line:
                return True

        return False

    def extract_category(self, text: str) -> str:
        """Определяет категорию продукта"""
        categories = {
            'Energy Diet': ['ED Smart', 'ED HD', 'Energy Diet'],
            'БАД': ['БАД', 'ББҚ', 'адаптоген', 'Адаптоген', 'Bio', 'Pro-indole',
                   'Be Best', 'Metabiotic', 'Lactoferra', 'Detox', 'Soft Sorb',
                   'Gelm', 'Greenflash', 'Key to health', 'PROHELPER', 'Omega-3'],
            'Коллаген': ['Collagen', 'коллаген'],
            'Похудение': ['Slim', '3D SLIM', 'Drain', 'похудени', 'арықтау'],
            'Чай': ['Tea', 'чай', 'шай', 'Enerwood'],
            'Косметика': ['косметика', 'Косметика', 'Be Loved', 'Biome',
                         'Occuba', 'The LAB', 'Sklaer', 'Smartum', 'Sun'],
            'Детские': ['Baby', 'Kids', 'детей', 'балалар', 'PROHELPER'],
            'Животные': ['Pets', 'животных', 'жануар'],
            'Дом': ['Fineffect', 'Textile']
        }

        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    return category

        return 'Другое'

    def parse_file(self, filepath: Path, page_num: int):
        """Парсит один файл каталога"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Разбиваем на строки
            lines = content.split('\n')

            # Очищаем от служебной информации
            clean_lines = []
            for line in lines:
                # Убираем нумерацию строк
                line = re.sub(r'^\s*\d+→', '', line)
                # Убираем лишние пробелы
                line = line.strip()
                if line and len(line) > 2:
                    clean_lines.append(line)

            # Объединяем в текст
            text = '\n'.join(clean_lines)

            # Ищем названия продуктов
            for line in clean_lines:
                if self.is_product_title(line):
                    # Сохраняем предыдущий продукт
                    if self.current_product:
                        self.products.append(self.current_product)

                    # Создаем новый продукт
                    self.current_product = {
                        'name': line,
                        'page': page_num,
                        'category': self.extract_category(text),
                        'description': '',
                        'price': None,
                        'pv': None,
                        'has_kz': 'KZ' in text or 'қазақ' in text.lower(),
                    }

            # Извлекаем цену и PV из текста страницы
            if self.current_product and self.current_product['page'] == page_num:
                price, pv = self.extract_price(text)
                if price:
                    self.current_product['price'] = price
                if pv:
                    self.current_product['pv'] = pv

                # Добавляем описание (первые 200 символов текста)
                description = ' '.join(clean_lines[:5])[:200]
                self.current_product['description'] = description

        except Exception as e:
            print(f"Ошибка при чтении {filepath}: {e}")

    def analyze_all_files(self):
        """Анализирует все файлы каталога"""
        print("Начинаю анализ каталога...")

        for i in range(1, 121):
            filename = f'pdf2text_page_{i:05d}.txt'
            filepath = CATALOG_DIR / filename

            if filepath.exists():
                self.parse_file(filepath, i)
                if i % 10 == 0:
                    print(f"Обработано страниц: {i}/120")

        # Сохраняем последний продукт
        if self.current_product:
            self.products.append(self.current_product)

        print(f"\nВсего найдено продуктов: {len(self.products)}")
        return self.products


class KnowledgeBaseAnalyzer:
    """Анализирует существующую базу знаний"""

    def __init__(self):
        self.existing_products = set()
        self.files = []

    def analyze(self):
        """Анализирует файлы в knowledge_base/products/"""
        print("\nАнализирую базу знаний...")

        if not KNOWLEDGE_BASE_DIR.exists():
            print(f"Папка {KNOWLEDGE_BASE_DIR} не найдена!")
            return

        # Читаем все .md файлы
        for filepath in KNOWLEDGE_BASE_DIR.glob('*.md'):
            self.files.append(filepath.name)

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Ищем упоминания продуктов
                # Продукты обычно в заголовках или списках
                lines = content.split('\n')
                for line in lines:
                    # Заголовки
                    if line.startswith('#'):
                        product = line.lstrip('#').strip()
                        if product and len(product) < 100:
                            self.existing_products.add(product.lower())

                    # Элементы списков
                    if line.strip().startswith('-') or line.strip().startswith('*'):
                        product = line.lstrip('-*').strip()
                        # Убираем цены и описания
                        product = re.split(r'[—–]', product)[0].strip()
                        if product and len(product) < 100:
                            self.existing_products.add(product.lower())

            except Exception as e:
                print(f"Ошибка при чтении {filepath}: {e}")

        print(f"Найдено файлов: {len(self.files)}")
        print(f"Упомянуто продуктов: {len(self.existing_products)}")

        return self.existing_products


def compare_and_report(catalog_products: List[Dict], kb_products: Set[str]):
    """Создает сравнительный отчет"""
    print("\nСоздаю отчет...")

    # Статистика
    total_catalog = len(catalog_products)
    products_with_price = [p for p in catalog_products if p['price']]
    products_without_price = [p for p in catalog_products if not p['price']]

    # Проверяем, какие продукты есть в базе
    missing_products = []
    found_products = []

    for product in catalog_products:
        name_lower = product['name'].lower()
        # Простая проверка по вхождению подстроки
        found = False
        for kb_product in kb_products:
            if name_lower in kb_product or kb_product in name_lower:
                found = True
                break

        if found:
            found_products.append(product)
        else:
            missing_products.append(product)

    # Группируем по категориям
    categories = {}
    for product in catalog_products:
        cat = product['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(product)

    # Создаем отчет
    report = f"""# Анализ каталога продуктов NL International

Дата анализа: {Path(__file__).stat().st_mtime}

## 1. Статистика

- **Всего продуктов в каталоге:** {total_catalog}
- **Продуктов с полной информацией (цена + PV):** {len([p for p in products_with_price if p['pv']])}
- **Продуктов только с ценой:** {len([p for p in products_with_price if not p['pv']])}
- **Продуктов без цены:** {len(products_without_price)}
- **Найдено в базе знаний:** {len(found_products)}
- **Отсутствует в базе знаний:** {len(missing_products)}

## 2. Категории продуктов

"""

    for cat, prods in sorted(categories.items()):
        report += f"\n### {cat} ({len(prods)} продуктов)\n\n"
        for p in prods[:5]:  # Показываем первые 5
            price_str = f"{p['price']} ₽" if p['price'] else "—"
            pv_str = f"{p['pv']} PV" if p['pv'] else "—"
            in_kb = "✓" if p in found_products else "✗"
            report += f"- [{in_kb}] **{p['name']}** (стр. {p['page']}) — {price_str} | {pv_str}\n"

        if len(prods) > 5:
            report += f"\n_...и еще {len(prods) - 5} продуктов_\n"

    report += "\n\n## 3. Продукты с полной информацией (цена + PV)\n\n"
    report += "| Название | Категория | Цена | PV | Страница | В базе? |\n"
    report += "|----------|-----------|------|----|----------|----------|\n"

    for p in products_with_price[:30]:  # Первые 30
        if p['pv']:
            in_kb = "✓" if p in found_products else "✗"
            report += f"| {p['name']} | {p['category']} | {p['price']} ₽ | {p['pv']} | {p['page']} | {in_kb} |\n"

    report += "\n\n## 4. Продукты БЕЗ цены (требуется дополнение)\n\n"
    report += "| Название | Категория | Описание | Страница | В базе? |\n"
    report += "|----------|-----------|----------|----------|----------|\n"

    for p in products_without_price[:30]:  # Первые 30
        in_kb = "✓" if p in found_products else "✗"
        desc = p['description'][:50] + '...' if len(p['description']) > 50 else p['description']
        report += f"| {p['name']} | {p['category']} | {desc} | {p['page']} | {in_kb} |\n"

    report += "\n\n## 5. Отсутствующие в базе знаний продукты\n\n"

    # Группируем отсутствующие по категориям
    missing_by_cat = {}
    for p in missing_products:
        cat = p['category']
        if cat not in missing_by_cat:
            missing_by_cat[cat] = []
        missing_by_cat[cat].append(p)

    for cat, prods in sorted(missing_by_cat.items()):
        report += f"\n### {cat} ({len(prods)} продуктов)\n\n"
        for p in prods:
            price_str = f" — {p['price']} ₽" if p['price'] else ""
            pv_str = f" ({p['pv']} PV)" if p['pv'] else ""
            report += f"- **{p['name']}** (стр. {p['page']}){price_str}{pv_str}\n"

    report += "\n\n## 6. Рекомендации\n\n"
    report += "### Приоритет 1: Создать файлы для популярных категорий\n\n"

    priority_categories = ['Energy Diet', 'БАД', 'Коллаген', 'Похудение', 'Косметика']
    for cat in priority_categories:
        if cat in missing_by_cat:
            count = len(missing_by_cat[cat])
            if count > 0:
                report += f"- **{cat}:** {count} продуктов не в базе\n"

    report += "\n### Приоритет 2: Дополнить существующие файлы\n\n"
    report += "Проверить и дополнить информацию о ценах и PV в существующих файлах.\n"

    report += "\n### Приоритет 3: Создать новые файлы\n\n"
    report += f"Всего продуктов без описания в базе знаний: {len(missing_products)}\n"

    # Сохраняем отчет
    report_path = PROJECT_ROOT / "CATALOG_ANALYSIS_REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nОтчет сохранен: {report_path}")

    # Сохраняем JSON с данными
    json_path = PROJECT_ROOT / "catalog_products.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(catalog_products, f, ensure_ascii=False, indent=2)

    print(f"Данные сохранены: {json_path}")


def main():
    """Основная функция"""
    print("=" * 60)
    print("Анализ каталога NL International")
    print("=" * 60)

    # Анализ каталога
    extractor = ProductExtractor()
    catalog_products = extractor.analyze_all_files()

    # Анализ базы знаний
    kb_analyzer = KnowledgeBaseAnalyzer()
    kb_products = kb_analyzer.analyze()

    # Создание отчета
    compare_and_report(catalog_products, kb_products)

    print("\n" + "=" * 60)
    print("Анализ завершен!")
    print("=" * 60)


if __name__ == '__main__':
    main()
