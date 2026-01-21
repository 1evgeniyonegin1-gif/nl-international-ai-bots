"""
Реферальные ссылки для воронки продаж

Ссылки владельца:
- Регистрация новичка (партнёра): https://nlstar.com/ref/eiPusg/
- Регистрация клиента: https://nlstar.com/ref/yWTYPC/
- Главная магазина: https://nlstar.com/ref/q9zfpK/
- ID партнёра: 007-6964987
"""

from shared.config.settings import settings


# Реферальные ссылки владельца бота
PARTNER_REGISTRATION_LINK = "https://nlstar.com/ref/eiPusg/"
CLIENT_REGISTRATION_LINK = "https://nlstar.com/ref/yWTYPC/"
SHOP_MAIN_LINK = "https://nlstar.com/ref/q9zfpK/"
PARTNER_ID = "007-6964987"


def get_registration_link() -> str:
    """Ссылка на регистрацию нового партнёра (в 1 линию)"""
    return PARTNER_REGISTRATION_LINK


def get_client_registration_link() -> str:
    """Ссылка на регистрацию клиента в интернет-магазине"""
    return CLIENT_REGISTRATION_LINK


def get_shop_link() -> str:
    """Главная страница интернет-магазина с реф.ссылкой"""
    return SHOP_MAIN_LINK


def get_partner_id() -> str:
    """ID партнёра для справки"""
    return PARTNER_ID


# Маппинг категорий продуктов на прямые ссылки в магазине
PRODUCT_CATEGORIES = {
    "energy_diet": f"{SHOP_MAIN_LINK}#energy-diet",
    "greenflash": f"{SHOP_MAIN_LINK}#greenflash",
    "beauty": f"{SHOP_MAIN_LINK}#beauty",
    "kids": f"{SHOP_MAIN_LINK}#kids",
    "sport": f"{SHOP_MAIN_LINK}#sport",
}


def get_product_category_link(category: str) -> str:
    """
    Возвращает ссылку на категорию продуктов

    Args:
        category: Категория (energy_diet, greenflash, beauty, kids, sport)

    Returns:
        Ссылка на категорию в магазине
    """
    return PRODUCT_CATEGORIES.get(category, SHOP_MAIN_LINK)


# Рекомендации продуктов по болям
PRODUCT_RECOMMENDATIONS = {
    "weight": {
        "name": "Energy Diet Smart",
        "description": "Контроль веса без голода и подсчёта калорий",
        "price_from": "3 500",
        "link": SHOP_MAIN_LINK,
        "benefits": [
            "25г белка на порцию",
            "200 ккал = полноценный приём пищи",
            "Все витамины и минералы",
            "Готовится за 2 минуты",
        ]
    },
    "energy": {
        "name": "Greenflash Витамины + Energy Diet",
        "description": "Энергия на весь день без кофеина",
        "price_from": "2 800",
        "link": SHOP_MAIN_LINK,
        "benefits": [
            "Комплекс витаминов группы B",
            "Поддержка нервной системы",
            "Естественная энергия",
            "Без привыкания",
        ]
    },
    "immunity": {
        "name": "Greenflash Иммунитет",
        "description": "Укрепление защитных сил организма",
        "price_from": "2 500",
        "link": SHOP_MAIN_LINK,
        "benefits": [
            "Витамин C, D, Цинк",
            "Натуральные экстракты",
            "Поддержка в сезон простуд",
            "Для всей семьи",
        ]
    },
    "beauty": {
        "name": "Greenflash Коллаген + Lovely косметика",
        "description": "Красота изнутри и снаружи",
        "price_from": "3 200",
        "link": SHOP_MAIN_LINK,
        "benefits": [
            "Морской коллаген",
            "Гиалуроновая кислота",
            "Витамины красоты",
            "Видимый результат за 2-4 недели",
        ]
    },
    "kids": {
        "name": "Energy Diet для детей",
        "description": "Полноценное питание для растущего организма",
        "price_from": "3 000",
        "link": SHOP_MAIN_LINK,
        "benefits": [
            "Вкусные коктейли",
            "Без сахара и красителей",
            "Витамины для роста",
            "Дети обожают!",
        ]
    },
    "sport": {
        "name": "Energy Diet Pro + Sport линейка",
        "description": "Питание для активных и спортсменов",
        "price_from": "4 000",
        "link": SHOP_MAIN_LINK,
        "benefits": [
            "Высокое содержание белка",
            "BCAA и аминокислоты",
            "Быстрое восстановление",
            "Для набора массы и сушки",
        ]
    },
}


def get_product_recommendation(pain_point: str) -> dict:
    """
    Возвращает рекомендацию продукта по боли клиента

    Args:
        pain_point: Боль клиента (weight, energy, immunity, beauty, kids, sport)

    Returns:
        Словарь с рекомендацией (name, description, price_from, link, benefits)
    """
    return PRODUCT_RECOMMENDATIONS.get(pain_point, PRODUCT_RECOMMENDATIONS["weight"])


def format_product_message(pain_point: str) -> str:
    """
    Форматирует сообщение с рекомендацией продукта

    Args:
        pain_point: Боль клиента

    Returns:
        Отформатированное сообщение с продуктом и ссылкой
    """
    product = get_product_recommendation(pain_point)

    benefits_text = "\n".join([f"• {b}" for b in product["benefits"]])

    return f"""<b>🎯 Рекомендую для тебя:</b>

<b>{product['name']}</b>
{product['description']}

<b>Что даёт:</b>
{benefits_text}

<b>💰 Цена от:</b> {product['price_from']} ₽

👉 <a href="{product['link']}">Заказать со скидкой 25%</a>

Или напиши мне любой вопрос — отвечу!"""
