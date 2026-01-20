# Инструкции для Claude Code

## Выбор модели: Sonnet vs Opus

**ВАЖНО:** Помогай пользователю выбирать правильную модель. Пользователь не программист.

### Когда рекомендовать Opus:
- Проектирование новой архитектуры
- Сложный дебаг (непонятно где проблема)
- Рефакторинг с изменением архитектуры
- Интеграция нескольких сложных систем
- Миграция на новые технологии
- Задачи где Sonnet уже ошибся
- Написание сложных алгоритмов

### Когда Sonnet достаточно:
- Исправление простых багов
- Добавление полей/кнопок/хендлеров по аналогии
- Изменение текстов, сообщений, конфигов
- Мелкие правки в существующих функциях
- Работа с переменными окружения

---

## О проекте

Система Telegram ботов для NL International:
- **AI-Куратор** (@nl_curator_bot) — персональный AI-ментор для партнёров
- **AI-Контент-Менеджер** (@nl_content_bot) — автогенерация и публикация контента

---

## Инфраструктура

### VPS Сервер (Timeweb Cloud)
- **IP:** 194.87.86.103
- **SSH:** `ssh root@194.87.86.103`
- **Путь проекта:** `/root/nl-international-ai-bots`
- **Systemd сервис:** `nl-bots.service`

### Команды управления сервером
```bash
# Подключение
ssh root@194.87.86.103

# Обновить код
cd /root/nl-international-ai-bots && git pull

# Перезапустить ботов
systemctl restart nl-bots

# Логи в реальном времени
journalctl -u nl-bots -f

# Статус
systemctl status nl-bots
```

### База данных
- **PostgreSQL:** localhost:5432
- **DB:** nl_international
- **User:** nlbot / postgres
- **Расширение:** pgvector (для RAG)

### Telegram
- **Группа с Topics:** -1003676349853
- **Боты:** @nl_curator_bot, @nl_content_bot
- **Админ ID:** 756877849

---

## AI Провайдеры

### YandexGPT (основной для контента)
- **Модель:** yandexgpt-lite (или yandexgpt для pro)
- **Credentials:** в `.env` (YANDEX_*)
- **Токены:** НЕ протухают (в отличие от GigaChat)
- **Оплата:** рублями

### YandexART (генерация изображений)
- **Включение:** `YANDEX_ART_ENABLED=true` в `.env`
- **Использует те же Yandex credentials**
- **Время генерации:** 30-60 сек

### GigaChat (резерв)
- **Проблема:** токен протухает каждые 30 дней
- **Если нужен:** обновить GIGACHAT_AUTH_TOKEN

---

## Структура проекта

```
nl-international-ai-bots/
├── curator_bot/                 # AI-Куратор
│   ├── main.py                 # Точка входа
│   ├── handlers/               # Команды и сообщения
│   └── ai/                     # Промпты и логика
│
├── content_manager_bot/         # Контент-Менеджер
│   ├── main.py                 # Точка входа
│   ├── handlers/               # admin.py, callbacks.py
│   ├── ai/                     # content_generator.py, prompts.py
│   ├── scheduler/              # Автопостинг
│   └── utils/                  # keyboards.py, image_helpers.py
│
├── shared/                      # Общий код
│   ├── config/settings.py      # ВСЕ настройки
│   ├── ai_clients/             # GigaChat, YandexGPT, YandexART, OpenAI...
│   ├── database/               # SQLAlchemy base
│   └── rag/                    # Векторный поиск
│
├── content/knowledge_base/      # База знаний RAG (200 документов)
├── scripts/                     # Утилиты (create_database.py, load_knowledge_base.py)
└── docs/                        # Документация
```

---

## Ключевые файлы

| Файл | Описание |
|------|----------|
| `shared/config/settings.py` | Все настройки из .env |
| `content_manager_bot/ai/prompts.py` | Промпты для генерации постов |
| `content_manager_bot/handlers/callbacks.py` | Обработчики кнопок |
| `content_manager_bot/scheduler/content_scheduler.py` | Автопостинг |
| `.env` | Переменные окружения (токены, ключи) |

---

## Команды ботов

### AI-Куратор
| Команда | Описание |
|---------|----------|
| `/start` | Регистрация |
| `/help` | Справка |
| `/progress` | Прогресс обучения |
| `/goal` | Установить цель |

### Контент-Менеджер
| Команда | Описание |
|---------|----------|
| `/generate` | Сгенерировать пост (выбор типа) |
| `/generate <тип>` | Сгенерировать конкретный тип |
| `/pending` | Посты на модерации |
| `/stats` | Статистика |
| `/schedule` | Настройки автопостинга |
| `/help` | Справка |

### Типы постов
- `product` — продукты NL
- `motivation` — мотивация
- `news` — новости
- `tips` — советы
- `success_story` — истории успеха
- `promo` — акции

---

## Topics группы (маппинг)

| Тип поста | Topic | ID |
|-----------|-------|-----|
| product | Продукты | TOPIC_PRODUCTS=7 |
| business | Бизнес | TOPIC_BUSINESS=6 |
| tips | Обучение | TOPIC_TRAINING=5 |
| news, promo | Новости | TOPIC_NEWS=4 |
| motivation, success_story | Истории успеха | TOPIC_SUCCESS=3 |
| faq | FAQ | TOPIC_FAQ=2 |

---

## Локальный запуск (Windows)

```bash
cd "c:\Users\mafio\OneDrive\Документы\projects\nl-international-ai-bots"

# Активировать venv
venv\Scripts\activate

# Запустить оба бота
python run_bots.py

# Или по отдельности:
python -m curator_bot.main
python -m content_manager_bot.main
```

---

## Деплой изменений

```bash
# 1. Закоммитить локально
git add .
git commit -m "описание"
git push

# 2. На сервере
ssh root@194.87.86.103
cd /root/nl-international-ai-bots
git pull
pip install -r requirements.txt  # если добавились зависимости
systemctl restart nl-bots
journalctl -u nl-bots -f  # проверить логи
```

---

## Переменные .env (актуальные)

```env
# Telegram
CURATOR_BOT_TOKEN=...
CONTENT_MANAGER_BOT_TOKEN=...
CHANNEL_USERNAME=@nl_Eleva
ADMIN_TELEGRAM_IDS=756877849

# Группа с Topics
GROUP_ID=-1003676349853
CURATOR_BOT_USERNAME=@nl_curator_bot
TOPIC_PRODUCTS=7
TOPIC_BUSINESS=6
TOPIC_TRAINING=5
TOPIC_NEWS=4
TOPIC_SUCCESS=3
TOPIC_FAQ=2

# YandexGPT (основной AI)
YANDEX_SERVICE_ACCOUNT_ID=aje76dc7i20078podfrc
YANDEX_KEY_ID=ajensd96tl0d2q9fqmp9
YANDEX_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...ключ...\n-----END PRIVATE KEY-----
YANDEX_FOLDER_ID=b1gibb3gjf11pjbu65r3
YANDEX_MODEL=yandexgpt-lite

# YandexART (генерация картинок)
YANDEX_ART_ENABLED=true
YANDEX_ART_WIDTH=1024
YANDEX_ART_HEIGHT=1024

# AI модели
CONTENT_MANAGER_AI_MODEL=YandexGPT  # или GigaChat
CURATOR_AI_MODEL=claude-3-5-sonnet-20241022

# База данных
DATABASE_URL=postgresql+asyncpg://postgres:UB8TG6%40%40IUYDGC@localhost:5432/nl_international

# GigaChat (резерв, токен протухает)
GIGACHAT_AUTH_TOKEN=...
GIGACHAT_CLIENT_ID=...
```

---

## Текущий статус (20 января 2026)

### Работает:
- AI-Куратор на VPS 24/7
- AI-Контент-Менеджер на VPS 24/7
- YandexGPT для генерации текста
- YandexART для генерации картинок
- Публикация в Topics группы
- RAG система (200 документов)
- Модерация постов (кнопки)
- Планирование публикаций

### TODO:
- [ ] Доделать автопостинг (кнопки /schedule не все работают)
- [ ] Переписать промпты (анализ рынка + стайлгайд)
- [ ] Добавить статистику просмотров/реакций

---

## Документация (актуальная)

| Файл | Содержание |
|------|------------|
| `CLAUDE.md` | **Этот файл** — главная инструкция |
| `README.md` | Общее описание проекта |
| `docs/VPS_DEPLOY.md` | Деплой на Timeweb VPS |
| `docs/DEPLOYMENT.md` | Все варианты деплоя |
| `docs/YANDEXGPT_SETUP.md` | Настройка YandexGPT (ключи!) |
| `docs/YANDEX_ART_INTEGRATION.md` | Генерация картинок |
| `docs/CONTENT_MANAGER_IMPLEMENTATION.md` | Техническая документация |

---

## Troubleshooting

### Бот не отвечает
1. Проверить статус: `systemctl status nl-bots`
2. Посмотреть логи: `journalctl -u nl-bots -n 50`
3. Перезапустить: `systemctl restart nl-bots`

### Ошибка AI "401 Unauthorized"
- **GigaChat:** токен протух → обновить GIGACHAT_AUTH_TOKEN
- **YandexGPT:** проверить YANDEX_FOLDER_ID и приватный ключ

### Пост публикуется не в тот топик
- Проверить GROUP_ID (должен начинаться с -100)
- Проверить TOPIC_* переменные в .env

### Картинки не генерируются
- Проверить YANDEX_ART_ENABLED=true
- Проверить логи на ошибки YandexART
