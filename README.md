# NL International AI Bots

Система AI-ботов для автоматизации бизнеса NL International.

**Статус:** Работает 24/7 на VPS (194.87.86.103)

---

## Боты в системе

### 1. AI-Куратор (@nl_curator_bot)
Персональный AI-ментор для партнёров NL International.

**Возможности:**
- Консультации по продуктам NL
- Помощь с бизнесом и маркетинг-планом
- Мотивация и поддержка 24/7
- RAG база знаний (200 документов)

### 2. AI-Контент-Менеджер (@nl_content_bot)
Автоматическая генерация и публикация контента.

**Возможности:**
- Генерация 6 типов постов (продукты, мотивация, новости, советы, истории успеха, акции)
- Генерация изображений (YandexART)
- Модерация контента перед публикацией
- Публикация в Topics группы
- Планирование публикаций

---

## Технологии

| Компонент | Технология |
|-----------|------------|
| Язык | Python 3.11+ |
| Telegram | aiogram 3.x |
| База данных | PostgreSQL + pgvector |
| AI текст | YandexGPT (основной), GigaChat (резерв) |
| AI картинки | YandexART |
| Хостинг | Timeweb Cloud VPS |

---

## Структура проекта

```
nl-international-ai-bots/
├── curator_bot/              # AI-Куратор
├── content_manager_bot/      # Контент-Менеджер
├── shared/                   # Общий код (config, ai_clients, rag)
├── content/knowledge_base/   # База знаний RAG
├── scripts/                  # Утилиты
└── docs/                     # Документация
```

---

## Быстрый старт

```bash
# Клонировать
git clone <repo-url>
cd nl-international-ai-bots

# Установить зависимости
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Настроить .env
copy .env.example .env
# Заполнить токены и ключи

# Создать БД
python scripts/create_database.py

# Запустить
python run_bots.py
```

---

## Документация

| Файл | Описание |
|------|----------|
| [CLAUDE.md](CLAUDE.md) | **Главная инструкция** — всё что нужно знать |
| [docs/VPS_DEPLOY.md](docs/VPS_DEPLOY.md) | Деплой на Timeweb VPS |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Все варианты деплоя |
| [docs/YANDEXGPT_SETUP.md](docs/YANDEXGPT_SETUP.md) | Настройка YandexGPT |
| [docs/YANDEX_ART_INTEGRATION.md](docs/YANDEX_ART_INTEGRATION.md) | Генерация изображений |
| [docs/CONTENT_MANAGER_IMPLEMENTATION.md](docs/CONTENT_MANAGER_IMPLEMENTATION.md) | Техническая документация |

---

## Команды ботов

### AI-Куратор
- `/start` — Регистрация
- `/help` — Справка
- `/progress` — Прогресс
- `/goal` — Установить цель

### Контент-Менеджер
- `/generate` — Сгенерировать пост
- `/pending` — Посты на модерации
- `/stats` — Статистика
- `/schedule` — Автопостинг
- `/help` — Справка

---

## Стоимость

| Компонент | Стоимость |
|-----------|-----------|
| VPS Timeweb | ~300 руб/мес |
| YandexGPT | Бесплатно до лимитов |
| YandexART | Бесплатно до лимитов |

---

## Лицензия

MIT
