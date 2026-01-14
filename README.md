# NL International AI Automation System

Система из двух AI-ботов для автоматизации бизнеса NL International.

## Что это?

**Бот 1: AI-Куратор** - Персональный ментор, который общается с каждым партнером в личных сообщениях, помогает с обучением, мотивирует, отвечает на вопросы 24/7.

**Бот 2: AI-Контент-менеджер** - Автоматически создает посты для Telegram-канала, анализирует конкурентов, публикует контент после вашего одобрения.

## Технологии

- Python 3.11+
- aiogram 3.x (Telegram Bot API)
- PostgreSQL + pgvector (база данных с векторным поиском)
- Gemini 1.5 Flash + GPT-3.5-turbo (AI модели)
- ChromaDB (векторная база знаний)

## Стоимость

- MVP: $7-15/месяц
- После 500+ пользователей: $20-30/месяц

## Быстрый старт

### 1. Установка зависимостей

```bash
# Создать виртуальное окружение
python -m venv venv

# Активировать (Windows)
venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt
```

### 2. Настройка

1. Скопируй `.env.example` в `.env`
2. Заполни токены ботов (получи у @BotFather)
3. Добавь API ключи для AI (Gemini/OpenAI)
4. Укажи свой Telegram ID

### 3. База данных

```bash
# Создать БД локально
python scripts/create_database.py

# Или использовать Railway/Render (они предоставят DATABASE_URL)
```

### 4. Загрузка базы знаний

```bash
# Положи все материалы NL в content/knowledge_base/
# Затем запусти:
python scripts/build_knowledge_base.py
```

### 5. Запуск ботов

```bash
# Куратор
python -m curator_bot.main

# Контент-менеджер (в другом терминале)
python -m content_manager_bot.main
```

## Документация

- [Руководство по Куратору](CURATOR_BOT.md)
- [Руководство по Контент-менеджеру](CONTENT_MANAGER_BOT.md)
- [Развертывание](DEPLOYMENT.md)

## Поддержка

Создай issue в GitHub или напиши в Telegram.

## Лицензия

MIT
