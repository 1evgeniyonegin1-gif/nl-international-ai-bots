# NL International AI Bots

Система AI-ботов для автоматизации бизнеса NL International.

---

## Боты в системе

### 1. AI-Куратор (@NL_Curator_Bot)
Персональный AI-ментор для партнёров NL International.

**Возможности:**
- Консультации по продуктам NL (нутрициология, БАДы, коллаген, похудение)
- Помощь с бизнесом и маркетинг-планом
- Мотивация и поддержка 24/7
- RAG база знаний с проверенной информацией о продуктах
- Персонализация под уровень партнёра

**AI модель:** GigaChat (Сбер) - бесплатно

### 2. AI-Контент-Менеджер (@nl_content_bot)
Автоматическая генерация и публикация контента в Telegram канал.

**Возможности:**
- Генерация 18 типов постов (продукты, мотивация, истории успеха, FAQ и др.)
- Генерация видео-кружочков и голосовых (8 типов кружочков, 3 типа голосовых)
- Модерация контента перед публикацией
- Планирование публикаций на конкретное время
- Редактирование и перегенерация через AI
- Автоматический планировщик публикаций
- Недельный контент-план (21 пост в неделю)

**AI модель:** GigaChat (Сбер) - бесплатно

---

## Технологии

| Компонент | Технология |
|-----------|------------|
| Язык | Python 3.11+ |
| Telegram | aiogram 3.x |
| База данных | PostgreSQL + SQLAlchemy 2.0 async |
| Векторный поиск | ChromaDB |
| AI | GigaChat (Сбер) - бесплатно |
| Планировщик | asyncio (встроенный) |

---

## Структура проекта

```
nl-international-ai-bots/
├── curator_bot/              # AI-Куратор
│   ├── main.py              # Точка входа
│   ├── handlers/            # Обработчики команд
│   ├── ai/                  # AI логика и промпты
│   └── rag/                 # RAG система (база знаний)
│
├── content_manager_bot/      # Контент-Менеджер
│   ├── main.py              # Точка входа
│   ├── handlers/            # Админ-команды и callbacks
│   ├── ai/                  # Генератор контента и промпты
│   ├── scheduler/           # Планировщик публикаций
│   └── database/            # Модели данных
│
├── shared/                   # Общий код
│   ├── config/              # Настройки (settings.py)
│   ├── database/            # База данных
│   ├── ai_clients/          # AI клиенты (GigaChat)
│   └── utils/               # Утилиты
│
├── content/                  # Контент
│   └── knowledge_base/      # База знаний для RAG
│       ├── products/        # Продукты NL
│       └── business/        # Бизнес-информация
│
├── scripts/                  # Скрипты
│   ├── create_database.py   # Создание таблиц
│   └── build_knowledge_base.py  # Индексация базы знаний
│
└── docs/                     # Документация
```

---

## Быстрый старт

### 1. Клонирование и установка

```bash
git clone <repo-url>
cd nl-international-ai-bots

# Создать виртуальное окружение
python -m venv venv

# Активировать (Windows)
venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt
```

### 2. Настройка .env

```bash
# Скопировать пример
copy .env.example .env

# Заполнить:
# - CURATOR_BOT_TOKEN (от @BotFather)
# - CONTENT_MANAGER_BOT_TOKEN (от @BotFather)
# - GIGACHAT_AUTH_TOKEN (от Сбер)
# - DATABASE_URL (PostgreSQL)
# - ADMIN_TELEGRAM_IDS (ваш ID)
# - CHANNEL_USERNAME (для публикаций)
```

### 3. База данных

```bash
# Создать таблицы
python scripts/create_database.py

# Индексировать базу знаний
python scripts/build_knowledge_base.py
```

### 4. Запуск ботов

```bash
# Куратор
python -m curator_bot.main

# Контент-менеджер (в другом терминале)
python -m content_manager_bot.main
```

---

## Стоимость

| Этап | Стоимость |
|------|-----------|
| Разработка и тестирование | Бесплатно |
| До 100 пользователей | $5-7/месяц (хостинг) |
| 100-500 пользователей | $10-15/месяц |
| 500+ пользователей | $20-30/месяц |

**GigaChat - полностью бесплатный!**

---

## Документация

- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Развёртывание 24/7
- [CONTENT_MANAGER_IMPLEMENTATION.md](docs/CONTENT_MANAGER_IMPLEMENTATION.md) - Техническая документация контент-менеджера
- [QUICKSTART.md](QUICKSTART.md) - Быстрый старт
- [START_HERE.md](START_HERE.md) - Начало работы

---

## База знаний (RAG)

Куратор использует RAG для точных ответов о продуктах:

| Категория | Файлы |
|-----------|-------|
| Продукты | `energy_diet.md`, `collagen.md`, `bady_i_adaptogeny.md`, `slim_pohudeniye.md` |
| Бизнес | `plan_voznagrazhdeniya.md` |

Добавление новых знаний:
1. Создать `.md` файл в `content/knowledge_base/`
2. Запустить `python scripts/build_knowledge_base.py`

---

## Команды ботов

### AI-Куратор
| Команда | Описание |
|---------|----------|
| `/start` | Регистрация и приветствие |
| `/help` | Справка |
| `/progress` | Прогресс обучения |
| `/goal` | Установить цель |

### Контент-Менеджер
| Команда | Описание |
|---------|----------|
| `/start` | Приветствие |
| `/generate` | Сгенерировать пост |
| `/pending` | Посты на модерации |
| `/stats` | Статистика |
| `/schedule` | Настройки автопостинга |
| `/help` | Справка |

---

## Лицензия

MIT

---

## Поддержка

Создайте issue в репозитории или напишите в Telegram.
