"""
Клиент для работы с Google Gemini API
"""
import google.generativeai as genai
from typing import List, Dict, Optional
from loguru import logger


class GeminiClient:
    """Клиент для взаимодействия с Gemini 1.5 Flash"""

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        """
        Инициализация клиента Gemini

        Args:
            api_key: API ключ Google AI
            model_name: Название модели (по умолчанию gemini-1.5-flash)
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        logger.info(f"Gemini client initialized with model: {model_name}")

    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> str:
        """
        Генерирует ответ от Gemini

        Args:
            system_prompt: Системная инструкция (роль AI)
            user_message: Сообщение пользователя
            context: История диалога в формате [{"role": "user", "content": "..."}, ...]
            temperature: Температура генерации (0-1, выше = более креативно)
            max_tokens: Максимальное количество токенов в ответе

        Returns:
            str: Ответ от AI
        """
        try:
            # Формируем полный промпт
            full_prompt = f"{system_prompt}\n\n"

            # Добавляем контекст (историю диалога)
            if context:
                for msg in context:
                    role = "Партнер" if msg["role"] == "user" else "Куратор"
                    full_prompt += f"{role}: {msg['content']}\n"

            # Добавляем текущее сообщение
            full_prompt += f"\nПартнер: {user_message}\nКуратор:"

            # Генерируем ответ
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )

            answer = response.text.strip()
            logger.debug(f"Gemini response: {answer[:100]}...")

            return answer

        except Exception as e:
            logger.error(f"Error generating Gemini response: {e}")
            raise

    async def generate_with_rag(
        self,
        system_prompt: str,
        user_message: str,
        knowledge_fragments: List[str],
        context: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Генерирует ответ с использованием базы знаний (RAG)

        Args:
            system_prompt: Системная инструкция
            user_message: Сообщение пользователя
            knowledge_fragments: Релевантные фрагменты из базы знаний
            context: История диалога
            temperature: Температура генерации

        Returns:
            str: Ответ от AI с учетом базы знаний
        """
        try:
            # Формируем промпт с базой знаний
            rag_prompt = f"{system_prompt}\n\n"
            rag_prompt += "=== РЕЛЕВАНТНАЯ ИНФОРМАЦИЯ ИЗ БАЗЫ ЗНАНИЙ ===\n"

            for i, fragment in enumerate(knowledge_fragments, 1):
                rag_prompt += f"\n[Фрагмент {i}]\n{fragment}\n"

            rag_prompt += "\n=== КОНЕЦ БАЗЫ ЗНАНИЙ ===\n\n"
            rag_prompt += "Используй информацию выше для ответа. Если информации недостаточно - честно скажи об этом.\n\n"

            # Добавляем контекст и сообщение
            if context:
                for msg in context:
                    role = "Партнер" if msg["role"] == "user" else "Куратор"
                    rag_prompt += f"{role}: {msg['content']}\n"

            rag_prompt += f"\nПартнер: {user_message}\nКуратор:"

            # Генерируем ответ
            response = self.model.generate_content(
                rag_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=1024,
                )
            )

            answer = response.text.strip()
            logger.info(f"Gemini RAG response generated successfully")

            return answer

        except Exception as e:
            logger.error(f"Error generating Gemini RAG response: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        """
        Подсчитывает количество токенов в тексте

        Args:
            text: Текст для подсчета

        Returns:
            int: Количество токенов
        """
        try:
            result = self.model.count_tokens(text)
            return result.total_tokens
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            # Примерная оценка: 1 токен ≈ 4 символа для русского языка
            return len(text) // 3
