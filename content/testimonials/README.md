# Testimonials — Чеки и истории партнёров

Эта папка содержит реальные чеки, фото "до/после" и истории партнёров NL International для использования в постах.

## Структура

```
testimonials/
├── checks/           # Чеки партнёров с суммами доходов
│   └── example_family_30k.jpg
│
├── before_after/     # Фото "до/после" результатов
│   └── example_weight_loss.jpg
│
└── stories/          # Фото партнёров с историями
    └── example_partner.jpg
```

## Как добавить новый testimonial

### Вручную (через файловую систему)

1. Положите фото в соответствующую папку (checks/before_after/stories)
2. Запустите скрипт индексации:

```bash
python scripts/index_testimonials.py
```

### Через бота (команда /upload_check)

```python
from shared.media import media_library

# Загрузить чек партнёра
await media_library.upload_testimonial(
    file_path="checks/ivanov_family_50k.jpg",
    description="Семья Ивановых, первый чек 50000₽ за месяц на 3D Slim",
    nl_products=["3d_slim", "omega"],
    category="checks",
    tags=["семья", "первый_чек", "успех"]
)
```

## Использование в постах

Testimonials автоматически используются в постах типа `success_story`:

```python
# Контент-менеджер автоматически выберет подходящий чек
testimonial = await media_library.get_testimonial(
    category="checks",
    tags=["успех"]
)
```

## Формат описаний

**Чеки (checks):**
- "Семья Петровых, чек 30000₽ за месяц"
- "Марина К., первый квалификационный чек 100000₽"

**До/После (before_after):**
- "Ирина, -15кг за 3 месяца на GreenFlash"
- "Андрей, трансформация за полгода"

**Истории (stories):**
- "Наталья, Москва — от менеджера до директора за год"
- "Олег, Казань — семейный бизнес на NL"

## Индексация

После добавления новых файлов запустите:

```bash
# Только testimonials
python scripts/index_testimonials.py

# Или полная переиндексация всей библиотеки
python scripts/index_media_library.py --force
```

## Требования к фото

- **Формат:** JPG, PNG
- **Размер:** до 10MB (Telegram limit)
- **Разрешение:** мин. 800x600px
- **Содержание:** чёткое, читаемое

## Конфиденциальность

⚠️ **ВАЖНО:** Размещайте только те фото, на которые есть согласие партнёра на публикацию!

- Спрашивайте разрешение перед публикацией
- Можно замазать ФИО/паспортные данные на чеках
- Не публикуйте личные телефоны/адреса
