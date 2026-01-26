# Быстрая настройка прокси для Claude API

## Проблема
Claude API возвращает **403 Forbidden** из России. Нужен прокси.

## Решение: Cloudflare Workers (бесплатно, 5 минут)

---

## Шаг 1: Создай Worker в Cloudflare

### 1.1 Регистрация
1. Открой: https://dash.cloudflare.com/sign-up
2. Создай аккаунт (любая почта)
3. Подтверди email

### 1.2 Создание Worker
1. В меню слева: **Workers & Pages**
2. Кнопка **Create** → **Create Worker**
3. Имя: `anthropic-proxy`
4. Нажми **Deploy**

### 1.3 Добавь код прокси
1. Нажми **Edit code** (или Quick Edit)
2. **Удали весь код** и вставь:

```javascript
export default {
  async fetch(request, env) {
    // Разрешаем OPTIONS для CORS
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "*",
        },
      });
    }

    // Только POST
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    // Проксируем на Anthropic
    const url = new URL(request.url);
    const targetUrl = "https://api.anthropic.com" + url.pathname + url.search;

    const headers = new Headers();
    for (const [key, value] of request.headers.entries()) {
      if (key.toLowerCase() !== "host") {
        headers.set(key, value);
      }
    }

    const response = await fetch(targetUrl, {
      method: "POST",
      headers: headers,
      body: request.body,
    });

    const responseHeaders = new Headers(response.headers);
    responseHeaders.set("Access-Control-Allow-Origin", "*");

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  },
};
```

3. Нажми **Save and deploy**

### 1.4 Скопируй URL
После деплоя увидишь URL:
```
https://anthropic-proxy.ВАШ_АККАУНТ.workers.dev
```

**Скопируй этот URL!**

---

## Шаг 2: Настрой локально

Отредактируй `.env`:

```env
# Добавь эту строку (замени URL на свой):
ANTHROPIC_BASE_URL=https://anthropic-proxy.ВАШ_АККАУНТ.workers.dev
```

Проверь:
```bash
python test_content_generation.py
```

Если видишь ответ от Claude без 403 — всё работает!

---

## Шаг 3: Задеплой на VPS

```bash
# Подключись
ssh root@194.87.86.103

# Отредактируй .env
cd /root/nl-international-ai-bots
nano .env

# Добавь строку:
# ANTHROPIC_BASE_URL=https://anthropic-proxy.ВАШ_АККАУНТ.workers.dev

# Сохрани: Ctrl+X, Y, Enter

# Перезапусти
systemctl restart nl-bots
journalctl -u nl-bots -f
```

---

## Проверка работы

В логах должно быть:
```
Anthropic client initialized with proxy: https://anthropic-proxy.ВАШ_АККАУНТ.workers.dev
Response generated successfully (tokens: input=..., output=...)
```

**Нет ошибок 403** = всё работает!

---

## Альтернатива: готовые публичные прокси (не рекомендуется)

Если очень срочно, можно временно использовать публичный прокси:

```env
# ВРЕМЕННО (может быть медленным и небезопасным)
ANTHROPIC_BASE_URL=https://api.anthropic-proxy.workers.dev
```

**Но лучше создать свой Worker** (5 минут, бесплатно, безопасно).

---

## Troubleshooting

### Worker не работает
1. Проверь URL — должен начинаться с `https://`
2. Проверь логи Worker: Cloudflare Dashboard → Workers → твой worker → Logs
3. Попробуй пересоздать Worker

### Всё равно 403
1. Убедись что `ANTHROPIC_BASE_URL` установлен в `.env`
2. Проверь что нет лишних пробелов в URL
3. Перезапусти бота: `systemctl restart nl-bots`

### Медленно работает
- Нормально, первый запрос может занять 2-3 сек (cold start)
- Последующие запросы быстрее

---

## Бонус: проверка статуса Worker

Открой в браузере:
```
https://anthropic-proxy.ВАШ_АККАУНТ.workers.dev/v1/messages
```

Должна быть ошибка **405 Method not allowed** (это нормально — Worker принимает только POST).

Если **404** — Worker не работает.
