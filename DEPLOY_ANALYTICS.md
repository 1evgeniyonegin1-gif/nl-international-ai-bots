# Деплой системы аналитики

## Быстрый старт

### 1. Применить миграцию БД

На VPS сервере:

```bash
# Подключиться к серверу
ssh root@194.87.86.103

# Перейти в директорию проекта
cd /root/nl-international-ai-bots

# Обновить код
git pull

# Применить миграцию
python scripts/migrate_analytics.py
```

### 2. Перезапустить боты

```bash
# Перезапустить сервис
systemctl restart nl-bots

# Проверить логи
journalctl -u nl-bots -f
```

### 3. Проверить работу

В Telegram боте `@nl_content_bot`:

1. Отправить `/help` - проверить новые команды
2. Отправить `/update_stats` - обновить статистику
3. Отправить `/analytics` - посмотреть дашборд

## Новые команды

| Команда | Описание |
|---------|----------|
| `/analytics [дней]` | Детальная аналитика за период |
| `/update_stats` | Обновить статистику из Telegram |
| `/top [критерий] [количество] [дней]` | Топ постов |

## Примеры использования

```bash
# Аналитика за 7 дней (по умолчанию)
/analytics

# Аналитика за 30 дней
/analytics 30

# Обновить статистику всех постов
/update_stats

# Топ-10 по вовлеченности за 30 дней
/top

# Топ-5 по просмотрам за 7 дней
/top views 5 7

# Топ-20 по реакциям за 90 дней
/top reactions 20 90
```

## Автоматическое обновление

Система автоматически обновляет статистику каждые 30 минут через планировщик.

Логи обновления:
```bash
journalctl -u nl-bots -f | grep "Stats updated"
```

## Что добавлено

### Модели данных
- Расширена модель `Post`:
  - `forwards_count` - пересылки
  - `reactions_breakdown` - разбивка реакций
  - `engagement_rate` - коэффициент вовлеченности
  - `last_metrics_update` - время обновления

- Новая модель `PostAnalytics` для исторических снимков

### Модули
- `content_manager_bot/analytics/stats_collector.py` - сбор статистики
- `content_manager_bot/analytics/analytics_service.py` - анализ данных

### Команды
- `/analytics` - детальная аналитика
- `/update_stats` - обновление статистики
- `/top` - топ постов

### Автоматизация
- Автообновление статистики каждые 30 минут
- Создание исторических снимков

## Troubleshooting

### Миграция не применилась

Проверить подключение к БД:
```bash
psql -h localhost -U postgres -d nl_international -c "\dt"
```

Применить миграцию вручную:
```bash
python scripts/migrate_analytics.py
```

### Статистика не обновляется

Проверить логи:
```bash
journalctl -u nl-bots -n 100 | grep -i "stats\|analytics"
```

Принудительно обновить:
```bash
# В боте
/update_stats
```

### Команды не работают

Проверить, что бот перезапущен:
```bash
systemctl status nl-bots
systemctl restart nl-bots
```

## Документация

Подробная документация: [docs/ANALYTICS.md](docs/ANALYTICS.md)

## Контакты

При проблемах проверить:
1. Логи: `journalctl -u nl-bots -f`
2. Статус: `systemctl status nl-bots`
3. БД: подключение и миграция
