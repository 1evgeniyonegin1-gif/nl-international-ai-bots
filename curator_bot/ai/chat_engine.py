"""
Основной AI движок для Куратора
"""
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger

from shared.ai_clients.openai_client import OpenAIClient
from curator_bot.ai.prompts import get_curator_system_prompt, get_rag_instruction
from curator_bot.database.models import User, ConversationMessage


class CuratorChatEngine:
    """
    Движок для генерации ответов куратора с использованием AI и RAG
    """

    def __init__(self, ai_client):
        """
        Инициализация движка

        Args:
            ai_client: Клиент для работы с AI (Gemini или OpenAI)
        """
        self.ai_client = ai_client
        logger.info("Curator chat engine initialized")

    async def generate_response(
        self,
        user: User,
        user_message: str,
        conversation_history: List[ConversationMessage],
        knowledge_fragments: Optional[List[str]] = None,
        max_history: int = 10
    ) -> str:
        """
        Генерирует ответ куратора

        Args:
            user: Объект пользователя
            user_message: Сообщение от пользователя
            conversation_history: История диалога
            knowledge_fragments: Релевантные фрагменты из базы знаний
            max_history: Максимальное количество сообщений из истории

        Returns:
            str: Ответ куратора
        """
        try:
            # Получаем системный промпт
            system_prompt = get_curator_system_prompt(
                user_name=user.first_name or "Партнер",
                qualification=user.qualification,
                lessons_completed=0,  # TODO: Считать из БД
                current_goal=user.current_goal
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
                    temperature=0.7
                )
            else:
                # Обычный ответ без базы знаний
                logger.info(f"Generating standard response for user {user.telegram_id}")
                response = await self.ai_client.generate_response(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    context=context,
                    temperature=0.7
                )

            logger.info(f"Response generated successfully for user {user.telegram_id}")
            return response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._get_fallback_response()

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
        if any(word in message_lower for word in ["продукт", "energy diet", "коктейль", "крем", "витамин"]):
            intent["category"] = "products"
            intent["keywords"].append("products")

        elif any(word in message_lower for word in ["заработ", "дохо", "товарообор", "проце", "бону", "квалифик"]):
            intent["category"] = "business"
            intent["keywords"].append("marketing_plan")

        elif any(word in message_lower for word in ["как продать", "клиент", "возражен", "продаж"]):
            intent["category"] = "sales"
            intent["keywords"].append("sales_scripts")

        elif any(word in message_lower for word in ["обучен", "урок", "курс", "мастер"]):
            intent["category"] = "training"

        elif any(word in message_lower for word in ["команд", "партнер", "структур", "лидер"]):
            intent["category"] = "team_building"

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
        # Используем RAG для вопросов о продуктах, бизнесе и продажах
        return intent["category"] in ["products", "business", "sales"]
