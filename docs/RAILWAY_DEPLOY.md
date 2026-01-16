# Деплой на Railway (24/7)

## Быстрый старт

### 1. Регистрация на Railway
1. Перейди на https://railway.app
2. Войди через GitHub

### 2. Создание проекта
1. Нажми **"New Project"**
2. Выбери **"Deploy from GitHub repo"**
3. Выбери репозиторий `nl-international-ai-bots`
4. Railway автоматически определит Python проект

### 3. Настройка переменных окружения

В Railway перейди в **Settings → Variables** и добавь:

```env
# Telegram Боты (ОБЯЗАТЕЛЬНО)
CURATOR_BOT_TOKEN=твой_токен_куратора
CONTENT_MANAGER_BOT_TOKEN=твой_токен_контент_менеджера
CHANNEL_USERNAME=@твой_канал

# Администраторы
ADMIN_TELEGRAM_IDS=твой_telegram_id

# База данных (Railway создаст автоматически)
DATABASE_URL=будет_создано_автоматически

# AI API ключи (минимум один)
GIGACHAT_AUTH_TOKEN=твой_gigachat_токен
# или
ANTHROPIC_API_KEY=твой_anthropic_ключ
# или
OPENAI_API_KEY=твой_openai_ключ

# Опционально
LOG_LEVEL=INFO
TIMEZONE=Europe/Moscow
```

### 4. Добавление PostgreSQL
1. В проекте нажми **"+ New"**
2. Выбери **"Database" → "PostgreSQL"**
3. Railway автоматически добавит `DATABASE_URL`

### 5. Деплой
- Railway автоматически задеплоит при пуше в GitHub
- Или нажми **"Deploy"** вручную

---

## Структура деплоя

```
railway.toml     - конфигурация Railway
Procfile         - команда запуска (worker)
run_bots.py      - скрипт запуска обоих ботов
```

---

## Мониторинг

### Логи
В Railway: **Deployments → View Logs**

### Статус ботов
- Зайди в Telegram к каждому боту
- Отправь `/start` - если отвечает, значит работает

---

## Стоимость

### Бесплатный тариф (Hobby)
- $5 кредитов/месяц бесплатно
- Достаточно для 2 ботов 24/7
- Нужна карта для верификации (не списывают)

### Платный (если нужно больше)
- $5-20/месяц в зависимости от нагрузки

---

## Решение проблем

### Бот не запускается
1. Проверь логи в Railway
2. Убедись что все переменные окружения заданы
3. Проверь что `DATABASE_URL` подключен

### Ошибка с БД
```bash
# Выполни миграции через Railway CLI
railway run python scripts/create_database.py
```

### Бот засыпает
- На Railway боты НЕ засыпают (в отличие от Render)
- Если есть проблемы - проверь `Procfile` (должен быть `worker`, не `web`)

---

## Railway CLI (опционально)

```bash
# Установка
npm install -g @railway/cli

# Логин
railway login

# Привязка проекта
railway link

# Деплой
railway up

# Логи
railway logs

# Запуск команд
railway run python scripts/create_database.py
```

---

## Альтернативный деплой: два сервиса

Если хочешь запускать ботов отдельно:

### Curator Bot
```bash
python -m curator_bot.main
```

### Content Manager Bot
```bash
python -m content_manager_bot.main
```

Создай два сервиса в Railway и укажи разные команды запуска.
