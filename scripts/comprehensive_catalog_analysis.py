#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Полный анализ каталога NL International и сравнение с базой знаний
Создает подробный отчет о недостающей и неполной информации
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Set
from collections import defaultdict

# Пути
PROJECT_ROOT = r"c:\Users\mafio\OneDrive\Документы\projects\nl-international-ai-bots"
CATALOG_DIR = os.path.join(PROJECT_ROOT, "полный каталог")
KNOWLEDGE_BASE_DIR = os.path.join(PROJECT_ROOT, "content", "knowledge_base", "products")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "MISSING_PRODUCT_INFO.md")

# Категории продуктов из каталога (страницы 92-99)
CATALOG_STRUCTURE = {
    "Коктейли": {
        "ED Smart 5 Classic": ["Ягодная панна-котта", "Шоколадный брауни", "Кофе", "Ванильный пломбир"],
        "ED Smart 4 Classic": ["Банановый сплит", "Вишневый брауни", "Черничный йогурт", "Лимонное печенье", "Ваниль", "Бельгийский шоколад", "Грушевый тарт"],
        "ED Smart 4 Milky": ["Арахис в карамели", "Кофе с молоком", "Фисташковое мороженое"],
        "Energy Diet HD": ["Банан", "Ваниль", "Капучино", "Клубника", "Кофе", "Соленая карамель", "Фисташка", "Шоколад", "Грибы", "Курица"],
        "Energy Pro": ["Протеин Ваниль", "Протеин Шоколад"],
        "Energy Life": ["Фруктовые батончики Финиковый MIX", "Фруктовые батончики Шоколадный MIX", "Протеиновые батончики"]
    },
    "Чай": {
        "Enerwood Classic": ["Black Tea", "Deep Black", "Green Tea", "Red Tea", "MIX Tea"],
        "Herbal Tea": ["Vodoley", "Lux", "Valery", "Liverpool", "Donna Bella", "Gentleman", "Prana"]
    },
    "Адаптогены": {
        "PH Balance Stones": ["устройство и картридж", "Сменный картридж"],
        "BioDrone": [],
        "BioTuning": [],
        "BioSetting": []
    },
    "Продукты для похудения": {
        "3D SLIM Program": ["DrainEffect Green", "DrainEffect Red Low Carb", "Кейс 3D SLIM Program"],
        "White Tea": ["SlimDose"],
        "3D SLIM cosmetics": ["Cold", "Hot", "Lifting", "Shaping"]
    },
    "БАД": {
        "Greenflash": [
            "Detox box plus", "Detox Step 1 plus", "Detox Step 2 plus", "Detox Step 3 plus",
            "Soft Sorb", "Gelm Cleanse", "Metabiotic", "Lactoferra", "Pro-indole",
            "Be Best male", "Be Best female",
            "Omega-3", "Vitamin D3 2000 ME", "Vitamin K2+D3", "Vitamin B9+B12",
            "Zinc", "Iron", "Vitamin C liposomal", "5-HTP liposomal",
            "Metabrain liposomal", "Neuromedium liposomal",
            "Calcium Marine", "Magnesium Marine", "Marine Collagen"
        ]
    },
    "Коллаген": {
        "Collagentrinity": [],
        "Collagen Peptides": [],
        "Marine Collagen": []
    },
    "Красота": {
        "Beauty blend": []
    },
    "Для детей": {
        "БАД": ["PROHELPER", "Mg+B6 for kids", "Omega-3 DHA Kids"],
        "Косметика": [
            "Средство для купания 3 в 1, 0+",
            "Молочко для тела детское, 0+",
            "Крем детский с пантенолом, 0+",
            "Гель для душа детский, 3+",
            "Шампунь детский, 3+",
            "Зубная паста детская, 2+"
        ]
    },
    "Для животных": {
        "Витамины": [
            "Общеукрепляющий комплекс для собак",
            "Общеукрепляющий комплекс для кошек",
            "Комплекс для кастрированных котов и стерилизованных кошек"
        ],
        "Косметика": [
            "Бережный шампунь для собак и кошек",
            "Спрей для легкого расчесывания"
        ]
    },
    "Косметика для лица": {
        "Be Loved Oriental": [
            "Гидрофильное масло", "Гидрофильный бальзам", "Пенка для умывания",
            "Увлажняющий мист", "Маска Glow", "Маска Detox гидрогелевая",
            "Обновляющие диски для лица", "Бабл-пудра",
            "Дневная увлажняющая сыворотка", "Увлажняющий крем-гель",
            "Крем для контура глаз", "Ночная сыворотка с ретинолом",
            "Обогащенный ночной крем", "Ночная маска для лица",
            "Гидрогелевые патчи Magic Glitter", "Гидрогелевые патчи Pink Glow",
            "Корректирующий CC-крем", "Бальзам для губ"
        ],
        "Biome": [
            "Сыворотка", "Крем для ухода за кожей вокруг глаз",
            "Двухфазный крем 2 in 1"
        ]
    },
    "Солнцезащитная косметика": {
        "Be Loved Sun": [
            "Крем солнцезащитный для лица SPF 50",
            "Крем солнцезащитный для тела SPF 50"
        ]
    },
    "Мужская косметика": {
        "The LAB male science": [
            "Гель для бритья", "Гель для душа и шампунь 2 в 1",
            "Гель для умывания", "Универсальный бальзам"
        ]
    },
    "Уход за телом": {
        "Be Loved Body": [
            "Увлажняющий гель и расслабляющий крем-гель для душа",
            "Питательное молочко", "Обновляющий скраб",
            "Насыщенный крем-баттер", "Смягчающий крем для рук",
            "Ухаживающий крем для ног"
        ],
        "Smartum Max": ["Восстанавливающий гель"],
        "Crispento": ["Дезодорант-кристалл для тела Silver"]
    },
    "Косметика для волос": {
        "Occuba Professional": [
            "Silky hair repair (Шампунь, Кондиционер, Маска)",
            "Shine Balance (Шампунь, Кондиционер)",
            "Volume & Strength (Шампунь, Кондиционер)",
            "Care&Protection Маска для волос",
            "Филлер для волос", "Крем-блеск", "Спрей-кондиционер",
            "Коллагеновый шампунь Color", "Коллагеновый шампунь Control",
            "Коллагеновый шампунь Repair", "Коллагеновый шампунь Volume",
            "Rich бальзам-кондиционер", "Cure маска",
            "Repair филлер", "Active сыворотка"
        ]
    },
    "Уход за полостью рта": {
        "Sklaer": [
            "Зубная паста Protect", "Зубная паста White",
            "Зубная паста Sensitive"
        ]
    },
    "Дом": {
        "Fineffect": [
            "Салфетка Floor", "Салфетка Polish", "Салфетка Shine",
            "Салфетка Soft", "Салфетка Superfiber", "Салфетка Universal",
            "Салфетка Universal plus", "Салфетка Auto",
            "Салфетка Multi-effect", "Губка Sponge"
        ]
    },
    "Аксессуары": {
        "Шейкеры": ["Шейкер ED Smart", "Шейкер NL"]
    },
    "Пользатека": {
        "Курсы": [
            "Антиэйдж", "Основы нутрициологии", "Сторителлинг",
            "Видео на коленке", "TIMEHACK: как всё успевать",
            "Конструктор твоей уверенности", "Целенавигатор",
            "Быстрокурс: пойми меня", "Как найти равновесие, когда неспокойно"
        ]
    }
}


def read_knowledge_base_files():
    """Читает все файлы из базы знаний и извлекает информацию о продуктах"""
    kb_path = Path(KNOWLEDGE_BASE_DIR)
    if not kb_path.exists():
        print(f"❌ Папка базы знаний не найдена: {KNOWLEDGE_BASE_DIR}")
        return {}

    kb_products = {}

    for file in kb_path.glob("*.md"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()

                # Извлекаем упоминания продуктов и информацию о них
                products_in_file = extract_products_from_text(content)

                kb_products[file.stem] = {
                    'file': file.name,
                    'content_length': len(content),
                    'products': products_in_file,
                    'has_prices': bool(re.search(r'\d+\s*₽', content)),
                    'has_pv': bool(re.search(r'\d+\.?\d*\s*PV', content, re.IGNORECASE)),
                    'has_composition': bool(re.search(r'(состав|компоненты|ингредиенты):', content, re.IGNORECASE)),
                    'has_usage': bool(re.search(r'(применение|способ применения|как применять|как использовать):', content, re.IGNORECASE)),
                    'has_benefits': bool(re.search(r'(преимущества|польза|эффект|действие):', content, re.IGNORECASE))
                }
        except Exception as e:
            print(f"Ошибка чтения {file}: {e}")

    return kb_products


def extract_products_from_text(text):
    """Извлекает упоминания продуктов из текста"""
    products = []

    # Паттерны для поиска названий продуктов
    patterns = [
        r'ED Smart\s+\d+\s+\w+',
        r'Energy Diet\s*\w*',
        r'Collagen\w*',
        r'BioDrone|BioSetting|BioTuning',
        r'Greenflash',
        r'Be Loved\s+\w+',
        r'Occuba',
        r'The LAB',
        r'Sklaer',
        r'Fineffect',
        r'Smartum Max',
        r'DrainEffect',
        r'White Tea',
        r'3D SLIM',
        r'Enerwood',
        r'Herbal Tea',
        r'Pro-indole',
        r'Beauty blend',
        r'Lactoferra',
        r'Metabiotic',
        r'PROHELPER',
        r'Omega-3',
        r'Vitamin [DABCK]\d*',
        r'Marine \w+',
        r'PH Balance Stones'
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        products.extend(matches)

    return list(set(products))


def flatten_catalog_structure():
    """Преобразует вложенную структуру каталога в плоский список продуктов"""
    all_products = []

    for category, subcategories in CATALOG_STRUCTURE.items():
        if isinstance(subcategories, dict):
            for brand, products in subcategories.items():
                if isinstance(products, list):
                    for product in products:
                        all_products.append({
                            'category': category,
                            'brand': brand,
                            'name': product if product else brand,
                            'full_name': f"{brand} {product}".strip()
                        })
                else:
                    all_products.append({
                        'category': category,
                        'brand': brand,
                        'name': brand,
                        'full_name': brand
                    })
        else:
            for item in subcategories:
                all_products.append({
                    'category': category,
                    'brand': category,
                    'name': item,
                    'full_name': item
                })

    return all_products


def compare_catalog_with_kb(catalog_products, kb_products):
    """Сравнивает каталог с базой знаний"""

    # Собираем все продукты из базы знаний
    kb_product_names = set()
    for kb_file, kb_data in kb_products.items():
        kb_product_names.update([p.lower() for p in kb_data['products']])

    # Анализируем каждый продукт из каталога
    missing_products = []
    incomplete_products = []

    for product in catalog_products:
        product_name = product['full_name'].lower()
        brand_name = product['brand'].lower()

        # Проверяем, есть ли продукт в базе знаний
        found_in_kb = False
        found_files = []

        for kb_file, kb_data in kb_products.items():
            kb_products_lower = [p.lower() for p in kb_data['products']]
            if any(product_name in kbp or kbp in product_name or brand_name in kbp for kbp in kb_products_lower):
                found_in_kb = True
                found_files.append({
                    'file': kb_file,
                    'has_prices': kb_data['has_prices'],
                    'has_pv': kb_data['has_pv'],
                    'has_composition': kb_data['has_composition'],
                    'has_usage': kb_data['has_usage'],
                    'has_benefits': kb_data['has_benefits']
                })

        if not found_in_kb:
            missing_products.append(product)
        elif found_files:
            # Проверяем полноту информации
            for file_info in found_files:
                if not all([file_info['has_composition'], file_info['has_usage'], file_info['has_benefits']]):
                    incomplete_products.append({
                        'product': product,
                        'file': file_info['file'],
                        'missing': {
                            'prices': not file_info['has_prices'],
                            'pv': not file_info['has_pv'],
                            'composition': not file_info['has_composition'],
                            'usage': not file_info['has_usage'],
                            'benefits': not file_info['has_benefits']
                        }
                    })

    return missing_products, incomplete_products


def generate_report(missing_products, incomplete_products, kb_products):
    """Генерирует подробный отчет в Markdown"""

    report = []
    report.append("# ОТЧЕТ: Анализ каталога NL International и базы знаний")
    report.append("")
    report.append(f"**Дата анализа:** 21 января 2026")
    report.append("")
    report.append("---")
    report.append("")

    # Статистика
    report.append("## Общая статистика")
    report.append("")
    catalog_total = len(flatten_catalog_structure())
    report.append(f"- **Продуктов в каталоге:** {catalog_total}")
    report.append(f"- **Файлов в базе знаний:** {len(kb_products)}")
    report.append(f"- **Отсутствуют в базе:** {len(missing_products)}")
    report.append(f"- **Неполная информация:** {len(incomplete_products)}")
    report.append("")
    report.append("---")
    report.append("")

    # Раздел 1: Новые продукты
    report.append("## 1. Новые продукты (есть в каталоге, НЕТ в базе знаний)")
    report.append("")

    if missing_products:
        # Группируем по категориям
        by_category = defaultdict(list)
        for product in missing_products:
            by_category[product['category']].append(product)

        for category, products in sorted(by_category.items()):
            report.append(f"### {category}")
            report.append("")
            for product in products:
                report.append(f"- ❌ **{product['full_name']}**")
                report.append(f"  - Нужно: описание, состав, назначение, применение")
                report.append("")
    else:
        report.append("✅ Все продукты из каталога есть в базе знаний!")
        report.append("")

    report.append("---")
    report.append("")

    # Раздел 2: Неполные данные
    report.append("## 2. Неполные данные (есть в базе, но мало информации)")
    report.append("")

    if incomplete_products:
        # Группируем по файлам
        by_file = defaultdict(list)
        for item in incomplete_products:
            by_file[item['file']].append(item)

        for file_name, items in sorted(by_file.items()):
            report.append(f"### Файл: `{file_name}.md`")
            report.append("")
            for item in items:
                product = item['product']
                missing = item['missing']
                report.append(f"- ⚠️ **{product['full_name']}**")
                missing_items = [k for k, v in missing.items() if v]
                if missing_items:
                    report.append(f"  - Отсутствует: {', '.join(missing_items)}")
                report.append("")
    else:
        report.append("✅ Вся информация в базе знаний полная!")
        report.append("")

    report.append("---")
    report.append("")

    # Раздел 3: Дубликаты
    report.append("## 3. Дубликаты (один продукт в нескольких файлах)")
    report.append("")

    # Ищем дубликаты
    product_to_files = defaultdict(list)
    for kb_file, kb_data in kb_products.items():
        for product in kb_data['products']:
            product_to_files[product.lower()].append(kb_file)

    duplicates = {k: v for k, v in product_to_files.items() if len(v) > 1}

    if duplicates:
        for product, files in sorted(duplicates.items()):
            report.append(f"- 🔄 **{product}**")
            report.append(f"  - Файлы: {', '.join([f'`{f}.md`' for f in files])}")
            report.append("")
    else:
        report.append("✅ Дубликатов не найдено!")
        report.append("")

    report.append("---")
    report.append("")

    # Раздел 4: Приоритетный список
    report.append("## 4. Приоритетный список для дополнения (ТОП-30)")
    report.append("")
    report.append("### Критичность: Высокая (ХИТ-продукты без полного описания)")
    report.append("")

    priority_products = [
        ("ED Smart", "Основной продукт для новичков"),
        ("Energy Diet HD", "Популярная линейка коктейлей"),
        ("Collagentrinity", "Инновационный коллаген"),
        ("Collagen Peptides", "Бестселлер красоты"),
        ("BioDrone", "Иммуностимулятор"),
        ("BioSetting", "Адаптоген для стресса"),
        ("BioTuning", "Адаптоген для энергии"),
        ("3D SLIM Program", "Комплекс для похудения"),
        ("DrainEffect", "Дренажный напиток"),
        ("White Tea SlimDose", "Контроль аппетита"),
        ("Greenflash Detox", "Программа детокса"),
        ("Be Loved Oriental", "Косметика для лица"),
        ("Biome", "Инновационная косметика"),
        ("Occuba Professional", "Профессиональный уход за волосами"),
        ("The LAB", "Мужская косметика"),
        ("Lactoferra", "Иммунитет и защита"),
        ("Pro-indole", "Женское и мужское здоровье"),
        ("Beauty blend", "Напиток красоты"),
        ("Metabiotic", "Здоровье ЖКТ"),
        ("Vitamin D3 2000 ME", "Базовый витамин"),
        ("Omega-3", "Для сердца и мозга"),
        ("Marine Collagen", "Морской коллаген"),
        ("5-HTP liposomal", "Липосомальные БАДы"),
        ("PROHELPER", "Детские витамины"),
        ("Omega-3 DHA Kids", "Омега для детей"),
        ("Enerwood Classic", "Авторские чаи"),
        ("Herbal Tea", "Фиточаи"),
        ("Smartum Max", "Восстанавливающий гель"),
        ("Fineffect", "Эко-текстиль для уборки"),
        ("Energy Life", "Полезные снеки")
    ]

    for i, (product, reason) in enumerate(priority_products, 1):
        report.append(f"{i}. **{product}**")
        report.append(f"   - Причина: {reason}")
        report.append("")

    report.append("---")
    report.append("")

    # Раздел 5: Проверка цен
    report.append("## 5. Проверка актуальности цен и PV")
    report.append("")
    report.append("### Файлы с ценами:")
    report.append("")

    files_with_prices = []
    files_without_prices = []

    for kb_file, kb_data in kb_products.items():
        if kb_data['has_prices'] and kb_data['has_pv']:
            files_with_prices.append(kb_file)
        else:
            files_without_prices.append(kb_file)

    if files_with_prices:
        for f in sorted(files_with_prices):
            report.append(f"- ✅ `{f}.md` (есть цены и PV)")
    report.append("")

    report.append("### Файлы БЕЗ цен:")
    report.append("")
    if files_without_prices:
        for f in sorted(files_without_prices):
            report.append(f"- ❌ `{f}.md` (нет цен или PV)")
    report.append("")

    report.append("⚠️ **ВАЖНО:** В текстовых файлах каталога (PDF) не обнаружены цены и PV баллы.")
    report.append("Необходимо получить актуальный прайс-лист в формате Excel или CSV.")
    report.append("")
    report.append("---")
    report.append("")

    # Рекомендации
    report.append("## 6. Рекомендации по улучшению базы знаний")
    report.append("")
    report.append("### Приоритет 1 (срочно)")
    report.append("")
    report.append("1. **Добавить цены и PV для всех продуктов**")
    report.append("   - Получить актуальный прайс-лист от NL")
    report.append("   - Обновить все файлы базы знаний")
    report.append("")
    report.append("2. **Дополнить ТОП-30 продуктов**")
    report.append("   - Полное описание")
    report.append("   - Состав")
    report.append("   - Способ применения")
    report.append("   - Противопоказания")
    report.append("")
    report.append("3. **Проставить даты актуальности**")
    report.append("   - Добавить метаданные `date_updated: YYYY-MM-DD`")
    report.append("   - Указать источник информации")
    report.append("")
    report.append("### Приоритет 2 (желательно)")
    report.append("")
    report.append("4. **Устранить дубликаты**")
    report.append("   - Объединить информацию из разных файлов")
    report.append("   - Создать единую структуру")
    report.append("")
    report.append("5. **Добавить изображения продуктов**")
    report.append("   - Создать референсы для image-to-image генерации")
    report.append("   - Сохранить в `content/product_images/`")
    report.append("")
    report.append("6. **Расширить информацию о программах**")
    report.append("   - Программы похудения")
    report.append("   - Программы детокса")
    report.append("   - Программы красоты")
    report.append("")
    report.append("---")
    report.append("")
    report.append("## Заключение")
    report.append("")
    report.append(f"**База знаний покрывает:** ~{100 - int(len(missing_products) / catalog_total * 100)}% каталога")
    report.append("")
    report.append("**Основные проблемы:**")
    report.append("1. Отсутствуют цены и PV (критично)")
    report.append("2. Не все продукты описаны (средняя критичность)")
    report.append("3. Неполная информация в существующих файлах (низкая критичность)")
    report.append("")
    report.append("**Следующие шаги:**")
    report.append("1. Получить актуальный прайс-лист с ценами и PV")
    report.append("2. Дополнить ТОП-30 приоритетных продуктов")
    report.append("3. Проставить даты актуальности во всех файлах")
    report.append("4. Добавить изображения продуктов для AI-генерации")
    report.append("")

    return "\n".join(report)


def main():
    print("=" * 80)
    print("АНАЛИЗ КАТАЛОГА NL INTERNATIONAL И БАЗЫ ЗНАНИЙ")
    print("=" * 80)
    print()

    # Шаг 1: Читаем базу знаний
    print("Чтение базы знаний...")
    kb_products = read_knowledge_base_files()
    print(f"   Найдено файлов: {len(kb_products)}")
    print()

    # Шаг 2: Формируем список продуктов из каталога
    print("Извлечение продуктов из каталога...")
    catalog_products = flatten_catalog_structure()
    print(f"   Найдено продуктов: {len(catalog_products)}")
    print()

    # Шаг 3: Сравниваем
    print("Сравнение каталога с базой знаний...")
    missing_products, incomplete_products = compare_catalog_with_kb(catalog_products, kb_products)
    print(f"   Отсутствуют в базе: {len(missing_products)}")
    print(f"   Неполная информация: {len(incomplete_products)}")
    print()

    # Шаг 4: Генерируем отчет
    print("Создание отчета...")
    report = generate_report(missing_products, incomplete_products, kb_products)

    # Сохраняем отчет
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"Отчет сохранен: {OUTPUT_FILE}")
    print()
    print("=" * 80)
    print("АНАЛИЗ ЗАВЕРШЕН")
    print("=" * 80)


if __name__ == "__main__":
    main()
