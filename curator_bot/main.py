"""
AI-Куратор - Главный файл бота
"""
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from shared.config.settings import settings
from shared.utils.logger import setup_logger
from shared.database.base import init_db
from curator_bot.handlers import messages, commands


# Настраиваем логгер
logger = setup_logger("curator", settings.log_level)


async def main():
    """Главная функция запуска бота"""

    logger.info("🚀 Starting AI-Curator Bot...")

    # Инициализируем базу данных
    logger.info("Initializing database...")
    await init_db()
    logger.info("✅ Database initialized")

    # Создаем бота
    bot = Bot(
        token=settings.curator_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Создаем диспетчер
    dp = Dispatcher()

    # Регистрируем роутеры
    dp.include_router(commands.router)
    dp.include_router(messages.router)

    logger.info("✅ Handlers registered")

    # Запускаем polling
    try:
        logger.info("🤖 AI-Curator Bot is running!")
        logger.info(f"Model: {settings.curator_ai_model}")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("👋 AI-Curator Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped by user")
