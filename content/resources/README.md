# Ресурсы для генерации контента

## Структура

### Логотипы
Поместите логотип NL International в эту папку:
- `nl_logo.png` - основной логотип (PNG с прозрачным фоном)
- Рекомендуемые размеры: 500x500 пикселей или больше
- Формат: PNG с альфа-каналом (прозрачность)

### Шрифты (опционально)
Если нужны кастомные шрифты для водяных знаков:
- `custom_font.ttf` - TrueType шрифт

## Использование

### Водяной знак (текст)
```python
from content_manager_bot.utils.image_helpers import add_watermark

result = add_watermark(
    base64_image=image_data,
    watermark_text="NL International",
    position="bottom_right",  # или "bottom_left", "top_right", "top_left", "center"
    opacity=128  # 0-255
)
```

### Наложение логотипа
```python
from content_manager_bot.utils.image_helpers import add_logo_overlay

result = add_logo_overlay(
    base64_image=image_data,
    logo_path="content/resources/nl_logo.png",
    position="bottom_right",
    logo_size_percent=10,  # 5-20%
    opacity=230  # 0-255
)
```

## Референсные изображения продуктов

Для использования image-to-image режима с реальными фото продуктов:

1. Поместите официальные фото продуктов в `content/product_images/`
2. Обновите `content/product_images/products_mapping.json`
3. Бот автоматически найдёт подходящий продукт по тексту поста

### Структура папок продуктов:
```
content/product_images/
├── greenflash/          # Витамины GreenFlash
│   ├── vision_plus.jpg
│   ├── multivitamin.jpg
│   ├── omega3.jpg
│   └── ...
├── lovely/              # Косметика Lovely
│   ├── face_cream.jpg
│   └── ...
├── energy_diet/         # Energy Diet
│   └── ...
└── other/               # Остальные продукты
    └── ...
```

## Примечания

- Все функции композитинга требуют установленной библиотеки **Pillow**
- Установка: `pip install Pillow`
- Если Pillow не установлена, функции вернут оригинальное изображение с предупреждением
