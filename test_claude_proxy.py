"""
Тест Claude через Cloudflare Workers прокси
"""
import asyncio
from loguru import logger
from shared.config.settings import settings
from shared.ai_clients.anthropic_client import AnthropicClient

async def test_claude():
    """Тест Claude через прокси"""

    logger.info("=" * 60)
    logger.info("ТЕСТ CLAUDE ЧЕРЕЗ ПРОКСИ")
    logger.info("=" * 60)

    logger.info(f"API Key: {settings.anthropic_api_key[:20]}...")
    logger.info(f"Proxy URL: {settings.anthropic_base_url}")
    logger.info(f"Model: {settings.content_manager_ai_model}")
    logger.info("")

    try:
        client = AnthropicClient()

        response = await client.generate_response(
            system_prompt="Ты - копирайтер для NL International. Пиши живо, с юмором, как Данил (21 год).",
            user_message="Напиши короткий мотивационный пост о том, что начать никогда не поздно. 200-300 символов. Используй HTML-теги: <blockquote>, <b>, <tg-spoiler>.",
            temperature=0.8,
            max_tokens=500
        )

        logger.success("✅ Claude ответил через прокси!")
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

if __name__ == "__main__":
    asyncio.run(test_claude())
