# Настройка Cloudflare Workers прокси для Anthropic API

## Зачем это нужно?
Anthropic API блокирует запросы с российских IP. Cloudflare Workers выступает промежуточным сервером и пропускает запросы.

**Бесплатный лимит:** 100,000 запросов/день — более чем достаточно.

---

## Шаг 1: Регистрация в Cloudflare

1. Перейди на https://dash.cloudflare.com/sign-up
2. Создай аккаунт (нужна почта)
3. Подтверди email

---

## Шаг 2: Создание Worker

1. После входа, в левом меню нажми **"Workers & Pages"**
2. Нажми кнопку **"Create"** (или "Create application")
3. Выбери **"Create Worker"**
4. Дай имя: `anthropic-proxy` (или любое другое)
5. Нажми **"Deploy"** (пока с дефолтным кодом)

---

## Шаг 3: Редактирование кода Worker

1. После деплоя нажми **"Edit code"** (или "Quick edit")
2. **Удали весь код** и вставь следующий:

```javascript
export default {
  async fetch(request, env) {
    // Разрешаем только POST запросы
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "POST, OPTIONS",
          "Access-Control-Allow-Headers": "*",
        },
      });
    }

    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    // Получаем путь запроса
    const url = new URL(request.url);
    const targetUrl = "https://api.anthropic.com" + url.pathname + url.search;

    // Копируем заголовки, кроме host
    const headers = new Headers();
    for (const [key, value] of request.headers.entries()) {
      if (key.toLowerCase() !== "host") {
        headers.set(key, value);
      }
    }

    // Проксируем запрос к Anthropic API
    const response = await fetch(targetUrl, {
      method: "POST",
      headers: headers,
      body: request.body,
    });

    // Возвращаем ответ с CORS заголовками
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

3. Нажми **"Save and deploy"**

---

## Шаг 4: Получение URL Worker

После деплоя ты увидишь URL вида:
```
https://anthropic-proxy.ВАШ_АККАУНТ.workers.dev
```

Скопируй этот URL.

---

## Шаг 5: Настройка на VPS

1. Подключись к серверу:
```bash
ssh root@194.87.86.103
```

2. Отредактируй .env:
```bash
nano /root/nl-international-ai-bots/.env
```

3. Добавь строку (замени URL на свой):
```
ANTHROPIC_BASE_URL=https://anthropic-proxy.ВАШ_АККАУНТ.workers.dev
```

4. Сохрани (Ctrl+X, Y, Enter)

5. Перезапусти ботов:
```bash
systemctl restart nl-bots
journalctl -u nl-bots -f
```

---

## Проверка работы

После перезапуска в логах должны быть успешные ответы от куратора без ошибок 403.

Если что-то не работает — проверь:
1. Правильный ли URL Worker в .env
2. Работает ли Worker (посмотри логи в Cloudflare Dashboard → Workers → твой worker → Logs)

---

## Безопасность (опционально)

Для дополнительной защиты можешь добавить проверку секретного ключа в Worker:

1. В Cloudflare: Workers → твой worker → Settings → Variables
2. Добавь переменную: `PROXY_SECRET` = `твой_секретный_ключ`

3. Обнови код Worker, добавив проверку в начало:
```javascript
// В начале функции fetch:
const proxySecret = request.headers.get("X-Proxy-Secret");
if (proxySecret !== env.PROXY_SECRET) {
  return new Response("Unauthorized", { status: 401 });
}
```

4. В .env на VPS добавь:
```
ANTHROPIC_PROXY_SECRET=твой_секретный_ключ
```

Это защитит твой прокси от использования посторонними.
