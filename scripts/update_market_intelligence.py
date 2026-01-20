#!/usr/bin/env python3
"""
Скрипт автоматического обновления маркетинговой аналитики.

Запускается раз в день (через cron/systemd timer).
Собирает:
- Новости NL International
- Информацию о конкурентах
- Тренды в нутрициологии и MLM
- Актуальные акции и промо

Добавляет данные в RAG базу знаний с метаданными о свежести.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict
import sys
from pathlib import Path

# Добавляем корневую директорию в путь для импорта модулей
sys.path.append(str(Path(__file__).parent.parent))

from shared.config.settings import settings
from shared.rag.vector_store import VectorStore

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/market_intelligence.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MarketIntelligenceCollector:
    """Сборщик маркетинговой аналитики"""

    def __init__(self):
        self.vector_store = VectorStore()
        self.today = datetime.now().strftime("%Y-%m-%d")

        # Источники для мониторинга
        self.sources = {
            "nl_official": {
                "name": "NL International официальный сайт",
                "url": "https://nl-international.ru/news/",
                "enabled": True
            },
            "competitors": [
                {
                    "name": "Herbalife Russia",
                    "keywords": ["herbalife", "гербалайф"],
                    "enabled": True
                },
                {
                    "name": "Siberian Wellness",
                    "keywords": ["siberian wellness", "сибирское здоровье"],
                    "enabled": True
                },
                {
                    "name": "Oriflame Wellness",
                    "keywords": ["oriflame wellness", "орифлейм"],
                    "enabled": True
                }
            ],
            "trends": [
                "нутрициология тренды 2026",
                "функциональное питание новости",
                "сетевой маркетинг россия",
                "БАДы исследования"
            ]
        }

    async def collect_all(self) -> Dict[str, List[str]]:
        """
        Собирает все данные из источников

        Returns:
            Dict со списками собранных документов по категориям
        """
        logger.info(f"🚀 Начало сбора маркетинговой аналитики {self.today}")

        results = {
            "nl_news": [],
            "competitor_insights": [],
            "industry_trends": [],
            "errors": []
        }

        try:
            # 1. Новости NL International
            logger.info("📰 Сбор новостей NL International...")
            nl_news = await self._collect_nl_news()
            results["nl_news"] = nl_news

            # 2. Анализ конкурентов
            logger.info("🔍 Анализ конкурентов...")
            competitor_data = await self._collect_competitor_insights()
            results["competitor_insights"] = competitor_data

            # 3. Отраслевые тренды
            logger.info("📊 Сбор трендов индустрии...")
            trends = await self._collect_industry_trends()
            results["industry_trends"] = trends

        except Exception as e:
            logger.error(f"❌ Ошибка при сборе данных: {e}")
            results["errors"].append(str(e))

        return results

    async def _collect_nl_news(self) -> List[str]:
        """Собирает новости с официального сайта NL"""
        # TODO: Реализовать парсинг новостей NL
        # Пока возвращаем заглушку

        # В идеале тут должен быть WebFetch или парсер
        # Для начала можно сделать через RSS если есть

        news_items = [
            f"""
            [НОВОСТЬ NL] {self.today}
            Источник: Официальный сайт NL International

            Примечание: Автоматический сбор новостей.
            Для полной реализации нужно настроить парсинг сайта или RSS.

            Категория: Новости компании
            Актуальность: Высокая
            """.strip()
        ]

        logger.info(f"✅ Собрано {len(news_items)} новостей NL")
        return news_items

    async def _collect_competitor_insights(self) -> List[str]:
        """Собирает информацию о конкурентах"""
        insights = []

        for competitor in self.sources["competitors"]:
            if not competitor["enabled"]:
                continue

            # TODO: Реализовать поиск через WebSearch
            # Пока заглушка

            insight = f"""
            [КОНКУРЕНТ: {competitor['name']}] {self.today}

            Анализ конкурента в сегменте MLM нутрициологии.

            Категория: Конкурентная аналитика
            Актуальность: Средняя
            """.strip()

            insights.append(insight)

        logger.info(f"✅ Собрано {len(insights)} инсайтов о конкурентах")
        return insights

    async def _collect_industry_trends(self) -> List[str]:
        """Собирает тренды индустрии"""
        trends = []

        for trend_query in self.sources["trends"]:
            # TODO: Реализовать WebSearch
            # Пока заглушка

            trend = f"""
            [ТРЕНД: {trend_query}] {self.today}

            Анализ трендов в нутрициологии и сетевом маркетинге.

            Категория: Отраслевые тренды
            Актуальность: Средняя
            """.strip()

            trends.append(trend)

        logger.info(f"✅ Собрано {len(trends)} трендов")
        return trends

    async def save_to_knowledge_base(self, data: Dict[str, List[str]]) -> int:
        """
        Сохраняет собранные данные в RAG базу знаний

        Args:
            data: Словарь с категориями и списками документов

        Returns:
            int: Количество сохраненных документов
        """
        total_saved = 0

        try:
            # Инициализируем RAG если нужно
            await self.vector_store.init_tables()

            logger.info(f"💾 Сохранение данных в RAG базу...")

            # Сохраняем новости NL
            for doc in data.get('nl_news', []):
                doc_id = await self.vector_store.add_document(
                    content=doc,
                    source="NL International",
                    category="market_intelligence_nl_news",
                    metadata={
                        "date": self.today,
                        "type": "nl_news",
                        "relevance": "high",
                        "auto_collected": True
                    }
                )
                if doc_id:
                    total_saved += 1
                    logger.debug(f"✅ Сохранена новость NL (ID: {doc_id})")

            # Сохраняем инсайты конкурентов
            for doc in data.get('competitor_insights', []):
                doc_id = await self.vector_store.add_document(
                    content=doc,
                    source="Competitor Analysis",
                    category="market_intelligence_competitors",
                    metadata={
                        "date": self.today,
                        "type": "competitor_insight",
                        "relevance": "medium",
                        "auto_collected": True
                    }
                )
                if doc_id:
                    total_saved += 1
                    logger.debug(f"✅ Сохранён инсайт конкурента (ID: {doc_id})")

            # Сохраняем тренды
            for doc in data.get('industry_trends', []):
                doc_id = await self.vector_store.add_document(
                    content=doc,
                    source="Industry Trends",
                    category="market_intelligence_trends",
                    metadata={
                        "date": self.today,
                        "type": "industry_trend",
                        "relevance": "medium",
                        "auto_collected": True
                    }
                )
                if doc_id:
                    total_saved += 1
                    logger.debug(f"✅ Сохранён тренд (ID: {doc_id})")

            logger.info(f"✅ Сохранено {total_saved} документов в RAG базу")

        except Exception as e:
            logger.error(f"❌ Ошибка при сохранении в базу знаний: {e}", exc_info=True)

        return total_saved

    async def cleanup_old_data(self, days_to_keep: int = 30):
        """
        Удаляет устаревшие данные из базы знаний

        Args:
            days_to_keep: Сколько дней хранить данные
        """
        from datetime import timedelta
        from sqlalchemy import delete

        logger.info(f"🧹 Очистка данных старше {days_to_keep} дней...")

        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            # Удаляем старые записи market_intelligence
            from shared.rag.vector_store import Document
            from shared.database.base import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                # Ищем документы с категорией market_intelligence старше cutoff_date
                stmt = delete(Document).where(
                    Document.category.like('market_intelligence%')
                ).where(
                    Document.created_at < cutoff_date
                )

                result = await session.execute(stmt)
                await session.commit()

                deleted_count = result.rowcount
                logger.info(f"✅ Удалено {deleted_count} устаревших документов")

        except Exception as e:
            logger.error(f"❌ Ошибка при очистке: {e}", exc_info=True)

    async def generate_summary(self, data: Dict[str, List[str]]) -> str:
        """
        Генерирует краткий отчет о собранных данных

        Args:
            data: Словарь с категориями и списками документов

        Returns:
            str: Текст отчета
        """
        summary = f"""
        📊 ОТЧЕТ О МАРКЕТИНГОВОЙ АНАЛИТИКЕ
        Дата: {self.today}

        ═══════════════════════════════════

        📰 Новости NL International: {len(data.get('nl_news', []))}
        🔍 Инсайты конкурентов: {len(data.get('competitor_insights', []))}
        📊 Отраслевые тренды: {len(data.get('industry_trends', []))}

        ❌ Ошибки: {len(data.get('errors', []))}

        ═══════════════════════════════════

        Всего собрано документов: {sum(len(v) for k, v in data.items() if k != 'errors')}
        """.strip()

        if data.get('errors'):
            summary += "\n\n⚠️ ОШИБКИ:\n"
            for error in data['errors']:
                summary += f"- {error}\n"

        return summary


async def main():
    """Главная функция"""
    try:
        collector = MarketIntelligenceCollector()

        # Собираем данные
        data = await collector.collect_all()

        # Сохраняем в базу знаний
        saved_count = await collector.save_to_knowledge_base(data)

        # Очищаем старые данные
        await collector.cleanup_old_data(days_to_keep=30)

        # Генерируем отчет
        summary = await collector.generate_summary(data)
        logger.info(f"\n{summary}")

        logger.info("✅ Обновление маркетинговой аналитики завершено")

    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
