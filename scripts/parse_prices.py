"""
Скрипт парсинга цен из файла "цены на все продукты.txt"
Создаёт структурированную базу products_database.json
"""
import re
import json
from pathlib import Path


def parse_prices_file(input_path: str, output_path: str):
    """
    Парсит файл с ценами и создаёт JSON базу продуктов.

    Формат входного файла:
    Категория или Название
    Название продукта
    Цена ₽ + PV (например: 2 790 ₽19.5 PV)
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]

    products = []
    current_category = "Другое"
    i = 0

    # Категории по ключевым словам
    category_keywords = {
        "Energy Diet": ["ED Smart", "Energy Diet", "Коктейль", "Супы", "Шейкер"],
        "Greenflash БАД": ["Collagen", "Omega", "Vitamin", "Detox", "Marine", "Zinc", "Iron", "Metab", "БАД", "5-HTP", "Lactoferra", "BioDrone", "Bio"],
        "Косметика Be Loved": ["Be Loved", "Biome", "Крем", "Сыворотка", "Маска", "Патчи", "Гель для умывания", "Бальзам для губ", "Мист", "Пенка"],
        "Уход за телом": ["для душа", "для тела", "для ног", "для рук", "Скраб", "Антицеллюлитный"],
        "Уход за волосами": ["Шампунь", "Кондиционер", "Маска для волос", "Occuba", "Silky hair"],
        "Для детей NLka": ["NLka", "Happy Smile", "Kids", "детск", "Omega-3 DHA"],
        "3D Slim": ["3D Slim", "DrainEffect", "Metaboost", "SlimDose"],
        "Чай и напитки": ["Чай", "Enerwood", "Фиточай", "Herbal"],
        "Для дома": ["Салфетка", "Губка", "для пола", "для посуды", "Уборка", "Стирка"],
        "Imperial Herb": ["GYAN", "Imperial Herb", "GUT VIGYAN", "LYMPH", "LIVO", "URI", "LUX"],
    }

    while i < len(lines):
        line = lines[i]

        # Пропускаем пустые строки и номера
        if not line or line.startswith('→') or re.match(r'^\d+→$', line):
            i += 1
            continue

        # Убираем номер в начале (формат: "123→Текст")
        clean_line = re.sub(r'^\d+→', '', line).strip()

        if not clean_line:
            i += 1
            continue

        # Проверяем, это категория или продукт
        # Категории обычно короткие и без цены
        is_category = len(clean_line) < 30 and not any(char in clean_line for char in ['₽', 'PV', '«', '»', ','])

        # Определяем категорию по ключевым словам
        for cat, keywords in category_keywords.items():
            if any(kw.lower() in clean_line.lower() for kw in keywords):
                current_category = cat
                break

        # Если похоже на категорию - обновляем текущую категорию
        if is_category and clean_line not in ["БАД", "Косметика", "Супы", "Шейкеры"]:
            # Это может быть подкатегория
            i += 1
            continue

        # Пробуем найти цену
        # Формат: "2 790 ₽19.5 PV" или "370 ₽" или "990 ₽6.5 PV"
        price_match = re.search(r'(\d[\d\s]*)\s*₽\s*([\d.]+)?\s*PV?', clean_line)

        if price_match:
            price_str = price_match.group(1).replace(' ', '')
            price = int(price_str)
            pv = float(price_match.group(2)) if price_match.group(2) else 0

            # Предыдущая строка - название продукта
            if i > 0:
                prev_line = re.sub(r'^\d+→', '', lines[i-1]).strip()
                # Если предыдущая строка - дубль, берём ещё раньше
                if i > 1:
                    prev_prev = re.sub(r'^\d+→', '', lines[i-2]).strip()
                    if prev_line == prev_prev:
                        name = prev_line
                    else:
                        name = prev_line
                else:
                    name = prev_line

                # Определяем категорию по названию продукта
                product_category = current_category
                for cat, keywords in category_keywords.items():
                    if any(kw.lower() in name.lower() for kw in keywords):
                        product_category = cat
                        break

                # Создаём ключ продукта (для поиска фото)
                product_key = name.lower()
                product_key = re.sub(r'[«»\'".,\-—–]', '', product_key)
                product_key = re.sub(r'\s+', '_', product_key)
                product_key = product_key[:50]  # Ограничиваем длину

                product = {
                    "name": name,
                    "price": price,
                    "pv": pv,
                    "category": product_category,
                    "key": product_key,
                    "price_per_portion": None
                }

                # Рассчитываем цену за порцию для коктейлей (15 порций)
                if "15 порций" in name or "порций" in name.lower():
                    portions_match = re.search(r'(\d+)\s*порци', name.lower())
                    if portions_match:
                        portions = int(portions_match.group(1))
                        product["price_per_portion"] = round(price / portions, 0)
                        product["portions"] = portions

                products.append(product)

        i += 1

    # Удаляем дубликаты по названию
    seen = set()
    unique_products = []
    for p in products:
        if p["name"] not in seen:
            seen.add(p["name"])
            unique_products.append(p)

    # Группируем по категориям
    categories = {}
    for p in unique_products:
        cat = p["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(p)

    # Сохраняем результат
    result = {
        "total_products": len(unique_products),
        "categories": categories,
        "products_list": unique_products
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Обработано {len(unique_products)} продуктов в {len(categories)} категориях")
    for cat, prods in categories.items():
        print(f"  {cat}: {len(prods)} продуктов")

    return result


if __name__ == "__main__":
    base_path = Path(__file__).parent.parent
    input_file = base_path / "цены на все продукты.txt"
    output_file = base_path / "content" / "products_database.json"

    # Создаём директорию если нет
    output_file.parent.mkdir(parents=True, exist_ok=True)

    parse_prices_file(str(input_file), str(output_file))
    print(f"\nБаза сохранена в: {output_file}")
