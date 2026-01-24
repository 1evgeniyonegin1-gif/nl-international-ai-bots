"""
Основной AI движок для Куратора с интегрированной системой персон.
Интегрирована диалоговая воронка для естественного ведения разговора.
"""
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

from shared.ai_clients.openai_client import OpenAIClient
from shared.persona import PersonaManager, PERSONA_CHARACTERISTICS
from curator_bot.ai.prompts import get_curator_system_prompt, get_rag_instruction
from curator_bot.database.models import User, ConversationMessage
from curator_bot.funnels.conversational_funnel import get_conversational_funnel, ConversationalFunnel


class CuratorChatEngine:
    """
    Движок для генерации ответов куратора с использованием AI и RAG.
    Интегрирована система персон для адаптации стиля общения.
    Интегрирована диалоговая воронка для естественного ведения разговора.
    """

    def __init__(self, ai_client):
        """
        Инициализация движка

        Args:
            ai_client: Клиент для работы с AI (Gemini или OpenAI)
        """
        self.ai_client = ai_client

        # Система персон для адаптации стиля
        self.persona_manager = PersonaManager()
        self.use_persona_system = True

        # Диалоговая воронка для естественного ведения разговора
        self.conversational_funnel = get_conversational_funnel()
        self.use_conversational_mode = True  # Включить диалоговый режим

        logger.info("Curator chat engine initialized with PersonaManager and ConversationalFunnel")

    async def generate_response(
        self,
        user: User,
        user_message: str,
        conversation_history: List[ConversationMessage],
        knowledge_fragments: Optional[List[str]] = None,
        max_history: int = 10,
        use_persona: bool = True
    ) -> str:
        """
        Генерирует ответ куратора

        Args:
            user: Объект пользователя
            user_message: Сообщение от пользователя
            conversation_history: История диалога
            knowledge_fragments: Релевантные фрагменты из базы знаний
            max_history: Максимальное количество сообщений из истории
            use_persona: Использовать систему персон для адаптации стиля

        Returns:
            str: Ответ куратора
        """
        try:
            # Получаем системный промпт
            system_prompt = get_curator_system_prompt(
                user_name=user.first_name or "Партнер",
                qualification=user.qualification,
                lessons_completed=user.lessons_completed,
                current_goal=user.current_goal
            )

            # Определяем температуру по умолчанию
            temperature = 0.7

            # Добавляем инструкции диалоговой воронки
            if self.use_conversational_mode:
                funnel_instructions = self.conversational_funnel.get_ai_instructions(
                    user_id=user.telegram_id,
                    message=user_message
                )
                system_prompt = system_prompt + "\n\n" + funnel_instructions
                logger.info(f"Added conversational funnel instructions for user {user.telegram_id}")

            # Добавляем контекст персоны если включена система
            if use_persona and self.use_persona_system:
                # Анализируем настроение сообщения пользователя и адаптируем персону
                persona_context = self._get_adaptive_persona(user_message)

                if persona_context:
                    # Добавляем информацию о персоне в промпт
                    persona_enhancement = self.persona_manager.get_prompt_enhancement(persona_context)
                    system_prompt = system_prompt + "\n\n" + persona_enhancement

                    # Используем температуру персоны
                    temperature = persona_context.temperature

                    logger.info(
                        f"Using persona {persona_context.persona_name} for user {user.telegram_id}"
                    )

            # Формируем контекст из истории диалога
            context = self._prepare_context(conversation_history, max_history)

            # Генерируем ответ
            if knowledge_fragments:
                # Используем RAG если есть фрагменты базы знаний
                logger.info(f"Generating RAG response for user {user.telegram_id}")
                response = await self.ai_client.generate_with_rag(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    knowledge_fragments=knowledge_fragments,
                    context=context,
                    temperature=temperature
                )
            else:
                # Обычный ответ без базы знаний
                logger.info(f"Generating standard response for user {user.telegram_id}")
                response = await self.ai_client.generate_response(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    context=context,
                    temperature=temperature
                )

            logger.info(f"Response generated successfully for user {user.telegram_id}")
            return response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._get_fallback_response()

    def _get_adaptive_persona(self, user_message: str):
        """
        Выбирает персону на основе контекста сообщения пользователя.

        Адаптирует стиль ответа под:
        - Эмоциональное состояние пользователя
        - Тип вопроса
        - Контекст разговора

        Args:
            user_message: Сообщение пользователя

        Returns:
            PersonaContext или None
        """
        message_lower = user_message.lower()

        # Определяем контекст по ключевым словам
        # Пользователь расстроен/устал -> tired или friend
        sad_keywords = ["устал", "не получается", "сложно", "трудно", "бросить", "не могу", "тяжело", "плохо"]
        if any(word in message_lower for word in sad_keywords):
            self.persona_manager.generate_mood(force_category="sadness", force_intensity="medium")
            return self.persona_manager.get_persona_context(post_type="personal")

        # Пользователь задаёт вопросы о продуктах -> expert
        product_keywords = ["продукт", "состав", "как принимать", "дозировка", "витамин", "коллаген", "energy diet"]
        if any(word in message_lower for word in product_keywords):
            self.persona_manager.generate_mood(force_category="interest", force_intensity="medium")
            return self.persona_manager.get_persona_context(post_type="product")

        # Пользователь скептик или сомневается -> expert или rebel
        skeptic_keywords = ["развод", "пирамида", "не верю", "зачем", "смысл", "почему так дорого", "обман"]
        if any(word in message_lower for word in skeptic_keywords):
            self.persona_manager.generate_mood(force_category="anger", force_intensity="light")
            return self.persona_manager.get_persona_context(post_type="myth_busting")

        # Пользователь радуется/делится успехом -> friend или crazy
        happy_keywords = ["получилось", "ура", "круто", "супер", "спасибо", "вау", "класс", "результат"]
        if any(word in message_lower for word in happy_keywords):
            self.persona_manager.generate_mood(force_category="joy", force_intensity="strong")
            return self.persona_manager.get_persona_context(post_type="celebration")

        # Пользователь спрашивает о бизнесе -> expert или friend
        business_keywords = ["заработать", "бизнес", "команда", "партнёр", "квалификация", "бонус", "доход"]
        if any(word in message_lower for word in business_keywords):
            self.persona_manager.generate_mood(force_category="trust", force_intensity="medium")
            return self.persona_manager.get_persona_context(post_type="business")

        # По умолчанию - дружелюбный стиль
        self.persona_manager.generate_mood(force_category="trust", force_intensity="light")
        return self.persona_manager.get_persona_context(post_type="tips")

    def _prepare_context(
        self,
        messages: List[ConversationMessage],
        max_messages: int
    ) -> List[Dict[str, str]]:
        """
        Подготавливает контекст из истории сообщений

        Args:
            messages: Список сообщений
            max_messages: Максимальное количество сообщений

        Returns:
            List[Dict]: Контекст в формате [{"role": "user", "content": "..."}]
        """
        # Берем последние N сообщений
        recent_messages = sorted(messages, key=lambda x: x.timestamp)[-max_messages:]

        context = []
        for msg in recent_messages:
            context.append({
                "role": "user" if msg.sender == "user" else "assistant",
                "content": msg.message_text
            })

        return context

    def _get_fallback_response(self) -> str:
        """Возвращает запасной ответ при ошибке"""
        return """Извини, у меня временные технические сложности 🔧

Я уже отправил уведомление техподдержке. Можешь задать вопрос немного позже, или напиши напрямую своему руководителю.

Спасибо за понимание!"""

    async def analyze_user_intent(self, user_message: str) -> Dict[str, any]:
        """
        Анализирует намерение пользователя

        Args:
            user_message: Сообщение пользователя

        Returns:
            Dict: Информация о намерении (type, category, urgency)
        """
        # Простая категоризация на основе ключевых слов
        message_lower = user_message.lower()

        intent = {
            "type": "general",
            "category": "other",
            "urgency": "normal",
            "keywords": []
        }

        # Определяем категорию вопроса
        # PRODUCTS - продукты NL International
        product_keywords = [
            "продукт", "energy diet", "коктейль", "крем", "витамин",
            "коллаген", "collagen", "бад", "адаптоген", "slim", "похуден",
            "косметик", "уход за кож", "сыворотк", "маск", "шампун",
            "гель", "лосьон", "тоник", "пилинг", "скраб", "капсул",
            "спрей", "напиток", "батончик", "чай", "кофе"
        ]
        if any(word in message_lower for word in product_keywords):
            intent["category"] = "products"
            intent["keywords"].append("products")

        # BUSINESS - маркетинг-план, заработок, партнёрство
        elif any(word in message_lower for word in [
            "заработ", "дохо", "товарообор", "проце", "бону", "квалифик",
            "маркетинг", "план вознаг", "карьер", "менеджер", "директор",
            "реферал", "пригласи", "ссылк", "промокод", "скидк", "регистр"
        ]):
            intent["category"] = "business"
            intent["keywords"].append("marketing_plan")

        # SALES - продажи и работа с возражениями
        elif any(word in message_lower for word in [
            "как продать", "клиент", "возражен", "продаж", "сетевой",
            "пирамид", "развод", "дорого", "не работает", "отказ"
        ]):
            intent["category"] = "sales"
            intent["keywords"].append("sales_scripts")

        # TRAINING - обучение, советы, соцсети
        elif any(word in message_lower for word in [
            "обучен", "урок", "курс", "мастер", "совет", "новичок",
            "начать", "первы шаг", "соцсет", "инстаграм", "telegram",
            "контент", "пост", "сторис", "reels", "видео"
        ]):
            intent["category"] = "training"
            intent["keywords"].append("training")

        # FAQ - заказы, доставка, оплата
        elif any(word in message_lower for word in [
            "заказ", "оформи", "доставк", "оплат", "получи", "посылк",
            "трек", "адрес", "пункт выдач", "почт", "курьер", "стоимость"
        ]):
            intent["category"] = "faq"
            intent["keywords"].append("faq")

        # COMPANY - о компании NL International
        elif any(word in message_lower for word in [
            "о компании", "nl international", "история", "основател",
            "когда создан", "сколько лет", "головной офис", "страны"
        ]):
            intent["category"] = "company"
            intent["keywords"].append("company")

        # TEAM_BUILDING - команда и структура
        elif any(word in message_lower for word in [
            "команд", "партнер", "структур", "лидер", "наставник", "спонсор"
        ]):
            intent["category"] = "team_building"
            intent["keywords"].append("team_building")

        # Определяем срочность
        if any(word in message_lower for word in ["срочно", "быстро", "важно", "помоги", "проблем"]):
            intent["urgency"] = "high"

        logger.debug(f"Intent analysis: {intent}")
        return intent

    def should_use_rag(self, intent: Dict[str, any]) -> bool:
        """
        Определяет, нужно ли использовать базу знаний для ответа

        Args:
            intent: Результат анализа намерения

        Returns:
            bool: True если нужно использовать RAG
        """
        # Используем RAG для всех категорий, связанных с NL International
        rag_categories = [
            "products",      # Продукты
            "business",      # Маркетинг-план, заработок
            "sales",         # Продажи, возражения
            "training",      # Обучение, соцсети
            "faq",           # Заказы, доставка
            "company",       # О компании
            "team_building"  # Команда (может быть в training)
        ]
        return intent["category"] in rag_categories
