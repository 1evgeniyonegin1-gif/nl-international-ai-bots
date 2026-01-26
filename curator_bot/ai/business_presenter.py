"""
Модуль для бизнес-презентации AI-Куратора

Отправляет фото чеков, истории успеха, презентации бизнеса.
Интегрируется с основным обработчиком сообщений.
"""
import json
import random
from pathlib import Path
from typing import Optional, List, Dict
from loguru import logger


# Путь к данным
BASE_PATH = Path(__file__).parent.parent.parent / "content" / "telegram_knowledge"


class BusinessPresenter:
    """
    Презентер бизнеса NL International.

    Умеет отправлять:
    - Истории успеха с фото
    - Фото чеков партнёров
    - Краткие презентации бизнес-модели
    """

    def __init__(self):
        self.success_stories: List[Dict] = []
        self.business_posts: List[Dict] = []
        self._load_content()

    def _load_content(self):
        """Загружает контент из JSON-файлов"""
        try:
            # Загружаем истории успеха (все, не только с фото)
            success_path = BASE_PATH / "success_stories.json"
            if success_path.exists():
                with open(success_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Берём все записи с высоким quality_score
                    self.success_stories = [
                        entry for entry in data.get("entries", [])
                        if entry.get("quality_score", 0) >= 60
                    ]
                    logger.info(f"Loaded {len(self.success_stories)} success stories")

            # Загружаем бизнес-посты
            business_path = BASE_PATH / "business.json"
            if business_path.exists():
                with open(business_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.business_posts = [
                        entry for entry in data.get("entries", [])
                        if entry.get("quality_score", 0) >= 60
                    ]
                    logger.info(f"Loaded {len(self.business_posts)} business posts")

        except Exception as e:
            logger.error(f"Error loading business content: {e}")

    def should_send_business_media(self, message: str, ai_response: str) -> Optional[str]:
        """
        Определяет, нужно ли отправить медиа для бизнес-презентации.

        Args:
            message: Сообщение пользователя
            ai_response: Ответ AI

        Returns:
            Тип медиа ('success_story', 'business_proof', 'income_proof') или None
        """
        message_lower = message.lower()
        response_lower = ai_response.lower()
        combined = f"{message_lower} {response_lower}"

        # Ключевые слова для разных типов медиа

        # Истории успеха — когда говорим о результатах
        success_keywords = [
            "результат", "похудел", "скинул", "минус", "кг",
            "получилось", "история", "пример", "отзыв"
        ]
        if any(kw in combined for kw in success_keywords):
            return "success_story"

        # Доказательства дохода — когда говорим о заработке
        income_keywords = [
            "заработок", "доход", "сколько платят", "сколько зарабат",
            "чек", "выплат", "получаешь", "бонус", "деньги", "бабки"
        ]
        if any(kw in combined for kw in income_keywords):
            return "income_proof"

        # Бизнес в целом — квалификации, команда
        business_keywords = [
            "бизнес", "партнёр", "партнер", "квалификац", "команд",
            "m1", "m2", "m3", "b1", "b2", "b3", "top", "регистр"
        ]
        if any(kw in combined for kw in business_keywords):
            return "business_proof"

        return None

    def get_success_story(self) -> Optional[str]:
        """
        Возвращает случайную историю успеха (только текст).

        Returns:
            Краткий текст истории или None
        """
        if not self.success_stories:
            return None

        story = random.choice(self.success_stories)
        text = self._shorten_text(story.get("text_cleaned", story.get("text", "")))
        return text

    def get_income_proof(self) -> Optional[str]:
        """
        Возвращает текст о доходе/заработке.

        Returns:
            Текст о заработке или None
        """
        # Ищем посты с упоминанием чеков/дохода
        income_posts = [
            post for post in self.business_posts
            if any(kw in post.get("text", "").lower()
                   for kw in ["чек", "выплат", "доход", "заработ", "бонус", "квалификац"])
        ]

        if not income_posts:
            income_posts = self.business_posts

        if not income_posts:
            return None

        post = random.choice(income_posts)
        text = self._shorten_text(post.get("text_cleaned", post.get("text", "")))
        return text

    def get_business_presentation(self) -> Optional[str]:
        """
        Возвращает общую бизнес-презентацию (текст).

        Returns:
            Текст презентации или None
        """
        if not self.business_posts:
            return None

        post = random.choice(self.business_posts)
        text = self._shorten_text(post.get("text_cleaned", post.get("text", "")))
        return text

    def _shorten_text(self, text: str, max_length: int = 500) -> str:
        """Сокращает текст до разумной длины для подписи к фото"""
        if len(text) <= max_length:
            return text

        # Обрезаем по последнему предложению
        shortened = text[:max_length]
        last_period = shortened.rfind(".")
        last_newline = shortened.rfind("\n")

        cut_point = max(last_period, last_newline)
        if cut_point > max_length // 2:
            return shortened[:cut_point + 1]

        return shortened + "..."

    def get_quick_business_pitch(self) -> str:
        """
        Возвращает краткую презентацию бизнеса (без фото).
        Для случаев когда нет подходящего фото.
        """
        pitches = [
            "Смотри как это работает: рекомендуешь продукты друзьям — получаешь процент. "
            "Чем больше людей — тем больше зарабатываешь. На M1 это 15-30к в месяц.",

            "NL — это не про продажи. Это про рекомендации. "
            "Сам пользуешься, рассказываешь другим, получаешь бонусы. Просто.",

            "Регистрация бесплатная. Покупаешь для себя со скидкой 25%, "
            "рекомендуешь друзьям — получаешь % от их покупок. Компании 25 лет.",

            "M1 = 750 баллов команды = 15-30к в месяц. "
            "M3 = 3000 баллов = 50-100к. Это реально, я сам прошёл этот путь."
        ]
        return random.choice(pitches)


# Глобальный экземпляр
business_presenter = BusinessPresenter()


def get_business_presenter() -> BusinessPresenter:
    """Возвращает глобальный экземпляр презентера"""
    return business_presenter
