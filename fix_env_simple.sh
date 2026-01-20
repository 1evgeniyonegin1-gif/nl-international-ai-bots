#!/bin/bash
# Быстрое исправление .env - удаляем пустые YANDEX переменные

cd /root/nl-international-ai-bots || exit 1

echo "Создаём бэкап .env..."
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

echo "Исправляем .env..."
# Удаляем строки с пустыми YANDEX переменными
sed -i '/^YANDEX_SERVICE_ACCOUNT_ID=$/d' .env
sed -i '/^YANDEX_KEY_ID=$/d' .env
sed -i '/^YANDEX_FOLDER_ID=$/d' .env
sed -i '/^YANDEX_PRIVATE_KEY=$/d' .env

echo ""
echo "Проверка YANDEX переменных:"
grep YANDEX .env | head -n 10

echo ""
echo "Перезапускаем боты..."
systemctl restart nl-bots

sleep 2
echo ""
echo "Статус ботов:"
systemctl status nl-bots --no-pager | head -n 20

echo ""
echo "Готово! Протестируйте /generate в боте."
