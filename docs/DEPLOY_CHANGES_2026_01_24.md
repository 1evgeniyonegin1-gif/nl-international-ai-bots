# Инструкция по деплою изменений (24 января 2026)

## Что изменилось

### 1. Куратор-бот: GigaChat → YandexGPT
- Куратор теперь использует YandexGPT-32k (как и контент-бот)
- Оба бота на одном API — это нормально, у нас грант 4000 руб
- Файл: `curator_bot/handlers/messages.py`

### 2. Форматирование: разделение стилей
- **Куратор**: НЕ использует markdown (чистый текст как в чате)
- **Контент**: Использует Telegram-форматирование (жирный, курсив, цитаты, спойлеры)

### 3. Фото продуктов: полный маппинг
- Создан `content/unified_products/full_products_mapping.json` (~200 продуктов)
- Файл: `curator_bot/utils/product_photos.py` полностью переписан

### 4. Парсер экспорта лидера
- Создан `content_manager_bot/utils/leader_topics.py`
- Темы берутся из экспорта ПО КАТЕГОРИЯМ (не рандом!)
- Нужно положить `result.json` в `content/leader_export/`

---

## Шаги деплоя

### 1. Подключиться к серверу

```bash
ssh root@194.87.86.103
cd /root/nl-international-ai-bots
```

### 2. Обновить код

```bash
git pull
```

### 3. Обновить .env на сервере

```bash
nano .env
```

**ОБЯЗАТЕЛЬНО ИЗМЕНИТЬ:**

```env
# Модель (ВАЖНО!)
YANDEX_MODEL=yandexgpt-32k

# Topic IDs (ПРОВЕРИТЬ что совпадают!)
GROUP_ID=-1003676349853
TOPIC_PRODUCTS=7
TOPIC_BUSINESS=6
TOPIC_TRAINING=5
TOPIC_NEWS=4
TOPIC_SUCCESS=3
TOPIC_FAQ=2
```

### 4. Перезапустить ботов

```bash
systemctl restart nl-bots
```

### 5. Проверить логи

```bash
journalctl -u nl-bots -f
```

---

## Проверка после деплоя

### Тест 1: Куратор — живой язык

Напишите боту `@nl_curator_bot`:
```
Хочу купить happy smile
```

**Ожидаемый ответ:**
```
О, отличный выбор! Happy Smile — это витаминки для детей в форме
конфеток. 790₽ за 60 штук, хватит на 2 месяца.
Вот ссылка для заказа: https://nlstar.com/ref/868Xyu/
```

**НЕ должно быть:**
- **Звёздочек** (markdown)
- Хештегов (#happysmile)
- Придуманных номеров телефонов
- Ссылок на nl.ru (только реферальные)

### Тест 2: Контент-бот публикует

```
/generate product
```

Проверить:
1. Пост создан с красивым форматированием
2. Кнопка "Опубликовать" работает
3. Пост появляется в ПРАВИЛЬНОМ топике (Продукты, не Истории успеха!)

### Тест 3: Фото продуктов

Напишите куратору:
```
Покажи Omega-3
```

Фото должно быть:
- `omega/omega/photos/*.jpg` (капсулы омега)
- НЕ `occuba/shampoo_balance` (бутылка шампуня)

---

## Если что-то не работает

### Бот не отвечает
```bash
systemctl status nl-bots
journalctl -u nl-bots -n 100
```

### Ошибка "401 Unauthorized" от YandexGPT
Проверить в .env:
- YANDEX_FOLDER_ID
- YANDEX_PRIVATE_KEY или YANDEX_PRIVATE_KEY_FILE
- YANDEX_KEY_ID
- YANDEX_SERVICE_ACCOUNT_ID

### Посты идут не в тот топик
Проверить в .env значения TOPIC_*:
```bash
grep TOPIC .env
```

Они должны совпадать с реальными ID тем в группе.
Узнать ID: отправить сообщение в тему, переслать боту @getmyid_bot.
