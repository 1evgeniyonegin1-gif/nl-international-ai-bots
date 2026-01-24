"""
Система управления настроением бота (Mood System).

Отвечает за:
- Генерацию ежедневного настроения
- Получение текущего настроения
- Триггеры изменения настроения
"""

import random
from datetime import datetime, date
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from content_manager_bot.database.models import MoodState
from .mood_config import (
    MOOD_CATEGORIES,
    MOOD_WEIGHTS,
    INTENSITY_DISTRIBUTION,
    get_personas_for_mood
)


class MoodSystem:
    """Управляет настроением бота"""

    def __init__(self, session: AsyncSession):
        """
        Args:
            session: AsyncSession для работы с БД
        """
        self.session = session

    async def get_current_mood(self) -> MoodState:
        """
        Получает текущее активное настроение.

        Если на сегодня нет настроения — генерирует новое.

        Returns:
            MoodState: Текущее настроение
        """
        today = date.today()

        # Ищем активное настроение на сегодня
        result = await self.session.execute(
            select(MoodState)
            .where(
                MoodState.is_active == True,
                MoodState.date >= datetime(today.year, today.month, today.day)
            )
            .order_by(MoodState.created_at.desc())
            .limit(1)
        )
        mood = result.scalar_one_or_none()

        if mood:
            return mood

        # Если нет — генерируем новое
        return await self.generate_daily_mood()

    async def generate_daily_mood(
        self,
        trigger: Optional[str] = None,
        force_category: Optional[str] = None,
        force_intensity: Optional[str] = None
    ) -> MoodState:
        """
        Генерирует новое настроение на день.

        Args:
            trigger: Событие-триггер (опционально)
            force_category: Принудительная категория (для тестирования)
            force_intensity: Принудительная интенсивность (для тестирования)

        Returns:
            MoodState: Новое настроение
        """
        # 1. Деактивировать предыдущие активные настроения
        await self._deactivate_previous_moods()

        # 2. Выбрать категорию настроения (с учётом весов)
        if force_category and force_category in MOOD_CATEGORIES:
            category = force_category
        else:
            category = self._select_category_weighted()

        # 3. Выбрать интенсивность
        if force_intensity and force_intensity in INTENSITY_DISTRIBUTION:
            intensity = force_intensity
        else:
            intensity = self._select_intensity()

        # 4. Выбрать конкретную эмоцию
        emotion = self._select_emotion(category, intensity)

        # 5. Выбрать версию персоны
        persona_version = self._select_persona(category, intensity)

        # 6. Создать и сохранить MoodState
        mood = MoodState(
            date=datetime.utcnow(),
            category=category,
            emotion=emotion,
            intensity=intensity,
            persona_version=persona_version,
            trigger=trigger,
            is_active=True
        )

        self.session.add(mood)
        await self.session.commit()
        await self.session.refresh(mood)

        print(f"[Mood System] 🎭 Новое настроение: {emotion} ({category}/{intensity}) → {persona_version}")

        return mood

    async def trigger_mood_change(
        self,
        event: str,
        force_category: Optional[str] = None
    ) -> MoodState:
        """
        Изменяет настроение по триггеру (событие).

        Примеры триггеров:
        - "big_achievement" → joy/extreme
        - "failure" → sadness/medium
        - "controversy" → anger/strong

        Args:
            event: Название события
            force_category: Категория настроения (опционально)

        Returns:
            MoodState: Новое настроение
        """
        # Маппинг событий → категории
        event_to_category = {
            "big_achievement": "joy",
            "small_win": "joy",
            "failure": "sadness",
            "setback": "sadness",
            "controversy": "anger",
            "frustration": "anger",
            "challenge": "anticipation",
            "new_opportunity": "excitement",
            "breakthrough": "surprise",
            "deep_thought": "calm"
        }

        # Маппинг событий → интенсивность
        event_to_intensity = {
            "big_achievement": "extreme",
            "small_win": "medium",
            "failure": "strong",
            "setback": "medium",
            "controversy": "strong",
            "frustration": "medium",
            "challenge": "medium",
            "new_opportunity": "strong",
            "breakthrough": "extreme",
            "deep_thought": "strong"
        }

        category = force_category or event_to_category.get(event)
        intensity = event_to_intensity.get(event, "medium")

        if not category:
            # Если событие неизвестно — рандомное настроение
            print(f"[Mood System] ⚠️ Неизвестное событие: {event}, генерирую рандомное настроение")
            return await self.generate_daily_mood(trigger=event)

        return await self.generate_daily_mood(
            trigger=event,
            force_category=category,
            force_intensity=intensity
        )

    async def _deactivate_previous_moods(self):
        """Деактивирует все предыдущие активные настроения"""
        result = await self.session.execute(
            select(MoodState).where(MoodState.is_active == True)
        )
        active_moods = result.scalars().all()

        for mood in active_moods:
            mood.is_active = False

        await self.session.commit()

    def _select_category_weighted(self) -> str:
        """Выбирает категорию настроения с учётом весов"""
        categories = list(MOOD_WEIGHTS.keys())
        weights = list(MOOD_WEIGHTS.values())

        return random.choices(categories, weights=weights, k=1)[0]

    def _select_intensity(self) -> str:
        """Выбирает интенсивность настроения"""
        intensities = list(INTENSITY_DISTRIBUTION.keys())
        probabilities = list(INTENSITY_DISTRIBUTION.values())

        return random.choices(intensities, weights=probabilities, k=1)[0]

    def _select_emotion(self, category: str, intensity: str) -> str:
        """Выбирает конкретную эмоцию из категории и интенсивности"""
        emotions = MOOD_CATEGORIES[category]["emotions"][intensity]
        return random.choice(emotions)

    def _select_persona(self, category: str, intensity: str) -> str:
        """Выбирает версию персоны на основе настроения"""
        personas = get_personas_for_mood(category, intensity)
        return random.choice(personas)

    async def get_mood_history(self, limit: int = 7) -> list[MoodState]:
        """
        Получает историю настроений.

        Args:
            limit: Количество записей (по умолчанию 7 дней)

        Returns:
            List[MoodState]: Список настроений
        """
        result = await self.session.execute(
            select(MoodState)
            .order_by(MoodState.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_mood_stats(self) -> dict:
        """
        Возвращает статистику настроений.

        Returns:
            dict: Статистика (категории, персоны, эмоции)
        """
        result = await self.session.execute(
            select(MoodState).order_by(MoodState.created_at.desc()).limit(30)
        )
        moods = list(result.scalars().all())

        if not moods:
            return {"total": 0, "categories": {}, "personas": {}, "emotions": {}}

        # Подсчёт категорий
        categories = {}
        for mood in moods:
            categories[mood.category] = categories.get(mood.category, 0) + 1

        # Подсчёт версий персоны
        personas = {}
        for mood in moods:
            personas[mood.persona_version] = personas.get(mood.persona_version, 0) + 1

        # Подсчёт эмоций
        emotions = {}
        for mood in moods:
            emotions[mood.emotion] = emotions.get(mood.emotion, 0) + 1

        return {
            "total": len(moods),
            "categories": categories,
            "personas": personas,
            "emotions": emotions
        }
