# Reference Images - Руководство по использованию

## Обзор

Система референсных изображений позволяет использовать **реальные фотографии продуктов** вместо полностью AI-генерированных изображений. Это решает проблему "галлюцинаций" AI, когда продукты выглядят неточно.

## Режимы работы

### 1. Text-to-Image (стандартный)
AI полностью генерирует изображение с нуля на основе текстового описания.

**Используется для:**
- Мотивационных постов
- Новостей
- Абстрактных концепций
- Когда нет референсного изображения

### 2. Image-to-Image (с референсом)
AI берёт реальное фото продукта и улучшает/стилизует фон, сохраняя продукт без изменений.

**Используется для:**
- Постов о конкретных продуктах NL
- Когда важна точность изображения продукта
- Когда есть официальное фото продукта

## Структура файлов

```
content/
├── product_images/              # Библиотека продуктов
│   ├── products_mapping.json   # Маппинг продуктов к изображениям
│   ├── greenflash/             # Витамины GreenFlash
│   │   ├── vision_plus.jpg
│   │   ├── multivitamin.jpg
│   │   ├── omega3.jpg
│   │   ├── vitamin_d3.jpg
│   │   └── collagen.jpg
│   ├── lovely/                 # Косметика Lovely
│   │   ├── face_cream.jpg
│   │   ├── serum.jpg
│   │   ├── micellar_water.jpg
│   │   └── body_lotion.jpg
│   ├── energy_diet/            # Energy Diet
│   │   ├── smart.jpg
│   │   ├── shake_chocolate.jpg
│   │   ├── shake_vanilla.jpg
│   │   └── soup.jpg
│   └── other/                  # Остальные продукты
│       ├── kids_vitamins.jpg
│       └── tea.jpg
└── resources/                   # Ресурсы (логотипы, шрифты)
    ├── nl_logo.png
    └── README.md
```

## Добавление новых продуктов

### Шаг 1: Добавьте фотографию

Поместите фото продукта в соответствующую категорию:
```bash
content/product_images/greenflash/new_product.jpg
```

**Требования к фото:**
- Формат: JPG или PNG
- Размер: минимум 800x800, рекомендуется 1024x1024+
- Качество: высокое, без сжатия
- Фон: желательно нейтральный (но не обязательно - AI может его изменить)
- Продукт: хорошо виден, в центре кадра

### Шаг 2: Обновите маппинг

Откройте `content/product_images/products_mapping.json` и добавьте запись:

```json
{
  "greenflash": {
    "new_product": {
      "name": "GreenFlash Новый Продукт",
      "image": "greenflash/new_product.jpg",
      "description": "Описание продукта для поиска"
    }
  }
}
```

### Шаг 3: Проверьте работу

Сгенерируйте пост о продукте через бота:
```
/generate product
```

В тексте поста упомяните название продукта - система автоматически найдёт референсное изображение.

## Автоматическое определение продукта

Система ищет упоминания продуктов в тексте поста по ключевым словам:

```python
# Примеры ключевых слов (уже настроено)
"vision", "зрение" → GreenFlash Vision Plus
"омега", "omega" → GreenFlash Omega-3
"коллаген" → GreenFlash Коллаген
"крем" → Lovely крем для лица
"energy diet" → Energy Diet Smart
```

Добавить новые ключевые слова можно в файле:
[content_manager_bot/utils/product_reference.py](../content_manager_bot/utils/product_reference.py) в методе `extract_product_from_content()`.

## Композитинг (Watermarks & Logos)

### Добавление текстового водяного знака

```python
from content_manager_bot.utils.image_helpers import add_watermark

result = add_watermark(
    base64_image=image_data,
    watermark_text="NL International",
    position="bottom_right",  # "bottom_left", "top_right", "top_left", "center"
    opacity=128  # 0-255, где 128 = полупрозрачный
)
```

### Наложение логотипа

```python
from content_manager_bot.utils.image_helpers import add_logo_overlay

result = add_logo_overlay(
    base64_image=image_data,
    logo_path="content/resources/nl_logo.png",
    position="bottom_right",
    logo_size_percent=10,  # 5-20% от ширины изображения
    opacity=230  # 0-255
)
```

**Требования к логотипу:**
- Формат: PNG с альфа-каналом (прозрачный фон)
- Размер: 500x500+ пикселей
- Качество: высокое

### Изменение размера изображения

```python
from content_manager_bot.utils.image_helpers import resize_image

result = resize_image(
    base64_image=image_data,
    max_width=1920,
    max_height=1920,
    quality=90  # Качество JPEG 1-100
)
```

## Использование в коде

### Базовая генерация (автоматически определяет режим)

```python
from content_manager_bot.ai.content_generator import ContentGenerator

generator = ContentGenerator()

# Генерация поста с автоопределением продукта
post_text, _ = await generator.generate_post(
    post_type="product",
    custom_topic="GreenFlash Vision Plus"
)

# Генерация изображения (автоматически использует image-to-image если найдёт продукт)
image_base64, prompt = await generator.generate_image(
    post_type="product",
    post_content=post_text,
    use_product_reference=True  # По умолчанию True
)

# Добавляем водяной знак
from content_manager_bot.utils.image_helpers import add_watermark
final_image = add_watermark(image_base64, "NL International", "bottom_right")
```

### Принудительно text-to-image (без референса)

```python
image_base64, prompt = await generator.generate_image(
    post_type="product",
    post_content=post_text,
    use_product_reference=False  # Отключить поиск референсов
)
```

### Ручной выбор референса

```python
from content_manager_bot.utils.product_reference import ProductReferenceManager

ref_manager = ProductReferenceManager()

# Получить base64 изображения продукта
ref_image = ref_manager.get_product_image_base64("vision_plus", "greenflash")

# Сгенерировать с конкретным референсом
from shared.ai_clients.yandexart_client import YandexARTClient

yandex_art = YandexARTClient()
image_base64 = await yandex_art.generate_image(
    prompt="Профессиональное фото продукта на студийном фоне",
    reference_image=ref_image
)
```

## Настройки в .env

```env
# YandexART должен быть включён
YANDEX_ART_ENABLED=true
YANDEX_ART_WIDTH=1024
YANDEX_ART_HEIGHT=1024

# Yandex Cloud credentials (те же что для YandexGPT)
YANDEX_SERVICE_ACCOUNT_ID=...
YANDEX_KEY_ID=...
YANDEX_PRIVATE_KEY=...
YANDEX_FOLDER_ID=...
```

## Установка зависимостей

```bash
# Pillow для композитинга (водяные знаки, логотипы)
pip install Pillow

# Или через requirements.txt
pip install -r requirements.txt
```

## Примеры использования

### Пример 1: Автоматический режим (рекомендуется)

```python
# Бот автоматически:
# 1. Генерирует текст поста о продукте
# 2. Ищет упоминание продукта в тексте
# 3. Находит референсное изображение
# 4. Использует image-to-image если нашёл, иначе text-to-image

generator = ContentGenerator()

post_text, _ = await generator.generate_post("product")
image_base64, prompt = await generator.generate_image("product", post_text)

# Результат: изображение с реальным продуктом на улучшенном фоне
```

### Пример 2: С композитингом

```python
from content_manager_bot.utils.image_helpers import add_watermark, add_logo_overlay

# Генерируем изображение
image_base64, _ = await generator.generate_image("product", post_text)

# Добавляем водяной знак
image_with_watermark = add_watermark(
    image_base64,
    "NL International",
    "bottom_right",
    opacity=100
)

# Добавляем логотип (если есть)
final_image = add_logo_overlay(
    image_with_watermark,
    "content/resources/nl_logo.png",
    "top_left",
    logo_size_percent=8
)
```

### Пример 3: Список всех продуктов

```python
from content_manager_bot.utils.product_reference import ProductReferenceManager

ref_manager = ProductReferenceManager()

# Получить все продукты
products = ref_manager.list_all_products()

for category, items in products.items():
    print(f"\n{category}:")
    for key, info in items.items():
        print(f"  - {info['name']}: {info['description']}")
```

## Troubleshooting

### Проблема: Продукт не находится автоматически

**Решение:**
1. Проверьте, что название продукта есть в тексте поста
2. Добавьте ключевые слова в `product_reference.py` → `extract_product_from_content()`
3. Или используйте ручной выбор референса

### Проблема: Изображение продукта не найдено

**Решение:**
1. Проверьте путь к файлу в `products_mapping.json`
2. Убедитесь что файл существует: `content/product_images/category/product.jpg`
3. Проверьте права доступа к файлу

### Проблема: Pillow не работает

**Решение:**
```bash
pip install --upgrade Pillow
```

Если продолжает не работать - функции вернут оригинальное изображение с предупреждением в логах.

### Проблема: YandexART не использует референс

**Решение:**
1. Проверьте что `use_product_reference=True` (по умолчанию)
2. Убедитесь что тип поста = "product"
3. Проверьте логи - должно быть сообщение "Using reference image for product..."

## API Reference

### ProductReferenceManager

```python
class ProductReferenceManager:
    def load_mapping() -> Dict
    def get_product_info(product_key: str, category: Optional[str]) -> Optional[Dict]
    def get_product_image_base64(product_key: str, category: Optional[str]) -> Optional[str]
    def find_product_by_name(product_name: str) -> Optional[tuple]
    def extract_product_from_content(content: str) -> Optional[tuple]
    def generate_image_to_image_prompt(product_info: Dict, original_prompt: str) -> str
```

### Image Helpers

```python
def add_watermark(base64_image: str, watermark_text: str, position: str, opacity: int) -> Optional[str]
def add_logo_overlay(base64_image: str, logo_path: str, position: str, logo_size_percent: int, opacity: int) -> Optional[str]
def resize_image(base64_image: str, max_width: int, max_height: int, quality: int) -> Optional[str]
```

## Что дальше?

1. **Добавьте фото всех продуктов NL** - чем больше продуктов в базе, тем лучше
2. **Разместите логотип** в `content/resources/nl_logo.png`
3. **Протестируйте** - создайте несколько постов о разных продуктах
4. **Настройте автоматизацию** - можно добавить водяные знаки автоматически при публикации

## Связанные файлы

- [content_generator.py](../content_manager_bot/ai/content_generator.py) - основная логика
- [product_reference.py](../content_manager_bot/utils/product_reference.py) - работа с референсами
- [image_helpers.py](../content_manager_bot/utils/image_helpers.py) - композитинг
- [yandexart_client.py](../shared/ai_clients/yandexart_client.py) - YandexART API
- [products_mapping.json](../content/product_images/products_mapping.json) - маппинг продуктов
