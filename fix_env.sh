#!/bin/bash
# Скрипт для исправления дублирующихся переменных в .env

cd /root/nl-international-ai-bots

# Бэкап
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Удаляем все YANDEX переменные
grep -v '^YANDEX' .env > .env.temp

# Добавляем правильные YANDEX переменные (без дублей)
cat >> .env.temp << 'EOF'

# YandexGPT credentials
YANDEX_SERVICE_ACCOUNT_ID=aje76dc7i20078podfrc
YANDEX_KEY_ID=ajensd96tl0d2q9fqmp9
YANDEX_PRIVATE_KEY_FILE=/root/nl-international-ai-bots/yandex_key.pem
YANDEX_FOLDER_ID=b1gibb3gjf11pjbu65r3
YANDEX_MODEL=yandexgpt-lite

# YandexART
YANDEX_ART_ENABLED=true
YANDEX_ART_WIDTH=1024
YANDEX_ART_HEIGHT=1024
EOF

# Заменяем
mv .env.temp .env

echo "✓ .env исправлен"
echo ""
echo "Проверка YANDEX переменных:"
grep YANDEX .env

echo ""
echo "Перезапускаем боты..."
systemctl restart nl-bots

echo ""
echo "Статус:"
systemctl status nl-bots --no-pager -l
