"""
Тестовый скрипт для проверки настроек и доступности AI
"""
import asyncio
from loguru import logger
from shared.config.settings import settings
from shared.ai_clients.yandexgpt_client import YandexGPTClient

async def test_settings():
    """Проверка настроек"""

    logger.info("=" * 60)
    logger.info("ПРОВЕРКА НАСТРОЕК")
    logger.info("=" * 60)

    logger.info(f"Content Manager AI Model: {settings.content_manager_ai_model}")
    logger.info(f"YandexGPT Model: {settings.yandex_model}")
    logger.info(f"YandexART Enabled: {settings.yandex_art_enabled}")
    logger.info(f"Yandex Folder ID: {settings.yandex_folder_id[:20]}...")
    logger.info("")

async def test_yandexgpt():
    """Тест YandexGPT"""

    logger.info("=" * 60)
    logger.info("ТЕСТ YANDEXGPT")
    logger.info("=" * 60)

    try:
        client = YandexGPTClient()
        logger.info(f"Используется модель: {client.model}")

        response = await client.generate_response(
            system_prompt="Ты - копирайтер для NL International. Пиши живо, с юмором.",
            user_message="Напиши короткий мотивационный пост о том, что начать никогда не поздно. 200-300 символов. Используй HTML-теги: <blockquote>, <b>, <tg-spoiler>.",
            temperature=0.8,
            max_tokens=500
        )

        logger.success("✅ Ответ получен!")
        logger.info("")
        logger.info("=" * 60)
        logger.info("РЕЗУЛЬТАТ:")
        logger.info("=" * 60)
        print(response)
        logger.info("=" * 60)
        logger.info(f"Длина: {len(response)} символов")

        # Проверяем наличие HTML-тегов
        has_blockquote = "<blockquote>" in response
        has_bold = "<b>" in response
        has_spoiler = "<tg-spoiler>" in response

        logger.info("")
        logger.info("Проверка форматирования:")
        logger.info(f"  <blockquote>: {'✅' if has_blockquote else '❌'}")
        logger.info(f"  <b>: {'✅' if has_bold else '❌'}")
        logger.info(f"  <tg-spoiler>: {'✅' if has_spoiler else '❌'}")

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

async def main():
    await test_settings()
    logger.info("")
    await test_yandexgpt()

if __name__ == "__main__":
    asyncio.run(main())
