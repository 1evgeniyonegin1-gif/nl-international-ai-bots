"""
Скрипт для создания базы данных
"""
import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.database.base import init_db
from shared.utils.logger import setup_logger

logger = setup_logger("db_init", "INFO")


async def main():
    """Создает все таблицы в базе данных"""
    try:
        logger.info("Creating database tables...")
        await init_db()
        logger.info("✅ Database tables created successfully!")

    except Exception as e:
        logger.error(f"❌ Error creating database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
