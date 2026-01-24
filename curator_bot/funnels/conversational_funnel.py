"""
Диалоговая воронка для AI-Куратора.

Полностью текстовый режим без кнопок.
Куратор сам определяет когда предложить продукт/бизнес.
Использует паттерны из скриптов продаж.
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from loguru import logger


class ConversationStage(Enum):
    """Этапы диалоговой воронки"""
    GREETING = "greeting"           # Приветствие, знакомство
    DISCOVERY = "discovery"         # Выявление болей и потребностей
    DEEPENING = "deepening"         # Углубление в проблему
    SOLUTION_HINT = "solution_hint" # Намёк на решение
    SOLUTION = "solution"           # Предложение продукта/бизнеса
    OBJECTION = "objection"         # Работа с возражениями
    CLOSING = "closing"             # Закрытие (CTA)
    FOLLOW_UP = "follow_up"         # Сопровождение


class UserIntent(Enum):
    """Намерение пользователя"""
    PRODUCT = "product"       # Интересуется продуктами
    BUSINESS = "business"     # Интересуется бизнесом
    SKEPTIC = "skeptic"       # Сомневается, скептик
    CURIOUS = "curious"       # Просто любопытен
    SUPPORT = "support"       # Нужна поддержка/помощь
    UNKNOWN = "unknown"       # Не определено


@dataclass
class ConversationContext:
    """Контекст диалога с пользователем"""
    user_id: int
    stage: ConversationStage = ConversationStage.GREETING
    intent: UserIntent = UserIntent.UNKNOWN

    # Выявленные боли и потребности
    pains: List[str] = field(default_factory=list)
    needs: List[str] = field(default_factory=list)
    objections: List[str] = field(default_factory=list)

    # Счётчики для определения готовности
    engagement_score: int = 0      # Насколько вовлечён
    trust_score: int = 0           # Насколько доверяет
    objection_count: int = 0       # Сколько возражений
    messages_count: int = 0        # Сколько сообщений обменялись

    # Предложенные решения
    suggested_products: List[str] = field(default_factory=list)
    suggested_business: bool = False

    # Таймстемпы
    last_message_at: Optional[datetime] = None
    conversation_started_at: Optional[datetime] = None


class ConversationalFunnel:
    """
    Диалоговая воронка — ведёт пользователя естественным разговором.

    Принципы:
    1. Сначала слушаем и задаём вопросы
    2. Выявляем боли органично
    3. Не предлагаем решение слишком рано
    4. Персонализируем под контекст
    """

    # Минимум сообщений до предложения решения
    MIN_MESSAGES_BEFORE_OFFER = 3

    # Порог доверия для предложения
    TRUST_THRESHOLD = 2

    # Маркеры для определения intent
    PRODUCT_MARKERS = [
        "устал", "энергия", "похудеть", "здоровье", "витамины", "кожа",
        "волосы", "сон", "иммунитет", "детокс", "спорт", "фитнес",
        "болит", "проблема", "хочу", "нужно", "посоветуй", "что лучше"
    ]

    BUSINESS_MARKERS = [
        "заработать", "дополнительный доход", "удалённо", "из дома",
        "бизнес", "подработка", "пассивный доход", "команда", "сетевой",
        "партнёр", "сколько можно заработать", "как начать"
    ]

    SKEPTIC_MARKERS = [
        "развод", "пирамида", "не верю", "обман", "дорого", "не работает",
        "млм", "сетевой маркетинг", "зачем", "почему", "бесполезно",
        "втюхивают", "навязывают", "секта"
    ]

    PAIN_MARKERS = {
        "energy": ["устаю", "нет сил", "энергии", "разбитый", "вялый", "сонный"],
        "weight": ["похудеть", "лишний вес", "жир", "живот", "фигура", "диета"],
        "skin": ["кожа", "прыщи", "морщины", "сухая", "проблемная", "возраст"],
        "immunity": ["болею", "простуда", "иммунитет", "слабый", "витамины"],
        "sleep": ["сон", "бессонница", "не высыпаюсь", "ночью", "утром тяжело"],
        "sport": ["спорт", "тренировки", "мышцы", "восстановление", "протеин"],
        "kids": ["ребёнок", "дети", "детский", "для детей", "малыш"],
        "money": ["заработок", "деньги", "доход", "финансы", "кредит", "ипотека"]
    }

    # Паттерны вопросов для углубления
    DEEPENING_QUESTIONS = {
        "energy": [
            "Давно тебя это беспокоит?",
            "А что обычно делаешь чтобы взбодриться?",
            "Утром тяжело или к вечеру накрывает?"
        ],
        "weight": [
            "Что уже пробовала?",
            "Какая цель — сколько хочешь сбросить?",
            "Диеты пробовала? Как результаты?"
        ],
        "money": [
            "Сколько времени готов уделять?",
            "Есть опыт в продажах или команде?",
            "Какой доход был бы комфортным для старта?"
        ]
    }

    # Переходные фразы к решению
    SOLUTION_HINTS = {
        "energy": "Знаешь, я сам через это прошёл. И нашёл один лайфхак...",
        "weight": "Понимаю. У меня многие клиенты с такой же историей. Есть один подход который реально работает...",
        "skin": "Слушай, у меня подруга с похожей проблемой была. Она нашла решение — расскажу?",
        "money": "Интересно. Я как раз работаю в системе где можно стартовать с минимумом и расти постепенно..."
    }

    def __init__(self):
        """Инициализация"""
        # Хранилище контекстов (в продакшене — Redis/DB)
        self._contexts: Dict[int, ConversationContext] = {}
        logger.info("ConversationalFunnel initialized")

    def get_context(self, user_id: int) -> ConversationContext:
        """Получает или создаёт контекст для пользователя"""
        if user_id not in self._contexts:
            self._contexts[user_id] = ConversationContext(
                user_id=user_id,
                conversation_started_at=datetime.now()
            )
        return self._contexts[user_id]

    def analyze_message(self, user_id: int, message: str) -> Dict[str, Any]:
        """
        Анализирует сообщение и обновляет контекст.

        Returns:
            Dict с рекомендациями для AI:
            - stage: текущий этап
            - intent: намерение пользователя
            - pains: выявленные боли
            - should_offer: готов ли к предложению
            - question_to_ask: вопрос для углубления
            - solution_hint: подводка к решению
        """
        ctx = self.get_context(user_id)
        message_lower = message.lower()

        # Обновляем счётчики
        ctx.messages_count += 1
        ctx.last_message_at = datetime.now()

        # Определяем intent если ещё не определён
        if ctx.intent == UserIntent.UNKNOWN:
            ctx.intent = self._detect_intent(message_lower)

        # Выявляем боли
        detected_pains = self._detect_pains(message_lower)
        for pain in detected_pains:
            if pain not in ctx.pains:
                ctx.pains.append(pain)

        # Определяем возражения
        if self._is_objection(message_lower):
            ctx.objection_count += 1
            objection = self._extract_objection(message_lower)
            if objection:
                ctx.objections.append(objection)

        # Обновляем engagement/trust
        ctx.engagement_score += self._calc_engagement_delta(message)
        ctx.trust_score += self._calc_trust_delta(message)

        # Определяем этап воронки
        ctx.stage = self._determine_stage(ctx)

        # Формируем рекомендации для AI
        result = {
            "stage": ctx.stage.value,
            "intent": ctx.intent.value,
            "pains": ctx.pains,
            "objections": ctx.objections,
            "messages_count": ctx.messages_count,
            "engagement": ctx.engagement_score,
            "trust": ctx.trust_score,
            "should_offer": self._should_offer_solution(ctx),
            "question_to_ask": None,
            "solution_hint": None,
            "objection_response": None
        }

        # Добавляем рекомендации по этапу
        if ctx.stage == ConversationStage.DISCOVERY and ctx.pains:
            # Задаём углубляющий вопрос
            pain = ctx.pains[-1]
            questions = self.DEEPENING_QUESTIONS.get(pain, [])
            if questions:
                import random
                result["question_to_ask"] = random.choice(questions)

        elif ctx.stage == ConversationStage.SOLUTION_HINT and ctx.pains:
            # Готовим подводку к решению
            pain = ctx.pains[0]
            result["solution_hint"] = self.SOLUTION_HINTS.get(pain)

        elif ctx.stage == ConversationStage.OBJECTION and ctx.objections:
            # Нужно отработать возражение
            result["objection_response"] = self._get_objection_script(ctx.objections[-1])

        logger.info(f"Conversation analysis for {user_id}: stage={ctx.stage.value}, intent={ctx.intent.value}")
        return result

    def _detect_intent(self, message: str) -> UserIntent:
        """Определяет намерение по сообщению"""
        if any(word in message for word in self.SKEPTIC_MARKERS):
            return UserIntent.SKEPTIC
        if any(word in message for word in self.BUSINESS_MARKERS):
            return UserIntent.BUSINESS
        if any(word in message for word in self.PRODUCT_MARKERS):
            return UserIntent.PRODUCT
        return UserIntent.CURIOUS

    def _detect_pains(self, message: str) -> List[str]:
        """Определяет боли из сообщения"""
        pains = []
        for pain_type, markers in self.PAIN_MARKERS.items():
            if any(word in message for word in markers):
                pains.append(pain_type)
        return pains

    def _is_objection(self, message: str) -> bool:
        """Проверяет, содержит ли сообщение возражение"""
        objection_markers = [
            "дорого", "не верю", "не работает", "развод", "пирамида",
            "нет времени", "подумаю", "не знаю", "сомневаюсь", "не уверен"
        ]
        return any(word in message for word in objection_markers)

    def _extract_objection(self, message: str) -> Optional[str]:
        """Извлекает тип возражения"""
        if any(word in message for word in ["дорого", "цена", "стоит"]):
            return "price"
        if any(word in message for word in ["не верю", "развод", "пирамида", "обман"]):
            return "trust"
        if any(word in message for word in ["нет времени", "занят"]):
            return "time"
        if any(word in message for word in ["подумаю", "потом"]):
            return "delay"
        return None

    def _calc_engagement_delta(self, message: str) -> int:
        """Считает изменение вовлечённости"""
        score = 0
        # Длинные сообщения = больше вовлечённости
        if len(message) > 100:
            score += 2
        elif len(message) > 50:
            score += 1
        # Вопросы = интерес
        if "?" in message:
            score += 1
        # Эмодзи = эмоциональная включённость
        if any(c for c in message if ord(c) > 127000):
            score += 1
        return score

    def _calc_trust_delta(self, message: str) -> int:
        """Считает изменение доверия"""
        score = 0
        message_lower = message.lower()

        # Позитивные маркеры
        if any(word in message_lower for word in ["спасибо", "интересно", "расскажи", "хочу"]):
            score += 1
        # Негативные маркеры
        if any(word in message_lower for word in ["не верю", "развод", "обман"]):
            score -= 1
        return score

    def _determine_stage(self, ctx: ConversationContext) -> ConversationStage:
        """Определяет текущий этап воронки"""
        if ctx.messages_count <= 1:
            return ConversationStage.GREETING

        if ctx.objection_count > 0 and ctx.objections:
            return ConversationStage.OBJECTION

        if not ctx.pains:
            return ConversationStage.DISCOVERY

        if ctx.messages_count < self.MIN_MESSAGES_BEFORE_OFFER:
            return ConversationStage.DEEPENING

        if self._should_offer_solution(ctx):
            if ctx.suggested_products or ctx.suggested_business:
                return ConversationStage.CLOSING
            return ConversationStage.SOLUTION

        return ConversationStage.SOLUTION_HINT

    def _should_offer_solution(self, ctx: ConversationContext) -> bool:
        """Определяет, готов ли пользователь к предложению"""
        # Нужно минимум сообщений
        if ctx.messages_count < self.MIN_MESSAGES_BEFORE_OFFER:
            return False

        # Нужен минимальный уровень доверия
        if ctx.trust_score < self.TRUST_THRESHOLD:
            return False

        # Должны быть выявлены боли
        if not ctx.pains:
            return False

        # Не предлагаем если много возражений
        if ctx.objection_count >= 3:
            return False

        return True

    def _get_objection_script(self, objection_type: str) -> str:
        """Возвращает скрипт для отработки возражения"""
        scripts = {
            "price": (
                "Понимаю. Давай посчитаем: {product} стоит X рублей на месяц. "
                "Это меньше чашки кофе в день. А результат — на всю жизнь."
            ),
            "trust": (
                "Слушай, я сам так думал сначала. Потом просто попробовал — и вот результат. "
                "Не призываю верить словам — попробуй один продукт и посмотри."
            ),
            "time": (
                "На самом деле это занимает 5 минут в день. "
                "Заварил порошок — выпил. Проще чем завтрак готовить."
            ),
            "delay": (
                "Конечно, подумай. Только вот что: пока думаем — время идёт, проблема остаётся. "
                "Может, попробуешь просто для эксперимента?"
            )
        }
        return scripts.get(objection_type, "")

    def get_ai_instructions(self, user_id: int, message: str) -> str:
        """
        Генерирует инструкции для AI на основе контекста.

        Вставляется в промпт перед генерацией ответа.
        """
        analysis = self.analyze_message(user_id, message)
        ctx = self.get_context(user_id)

        instructions = f"""
=== ДИАЛОГОВАЯ ВОРОНКА ===

ТЕКУЩИЙ ЭТАП: {analysis['stage']}
НАМЕРЕНИЕ ПОЛЬЗОВАТЕЛЯ: {analysis['intent']}
ВЫЯВЛЕННЫЕ БОЛИ: {', '.join(analysis['pains']) or 'ещё не выявлены'}
СООБЩЕНИЙ В ДИАЛОГЕ: {analysis['messages_count']}
УРОВЕНЬ ДОВЕРИЯ: {analysis['trust']}/5
ВОВЛЕЧЁННОСТЬ: {analysis['engagement']}/10

"""

        # Инструкции по этапу
        if analysis['stage'] == 'greeting':
            instructions += """
ТВОЯ ЗАДАЧА НА ЭТОМ ЭТАПЕ:
- Поприветствуй тепло и неформально
- Спроси как дела / что привело
- НЕ предлагай ничего, только слушай
"""

        elif analysis['stage'] == 'discovery':
            instructions += """
ТВОЯ ЗАДАЧА НА ЭТОМ ЭТАПЕ:
- Задавай открытые вопросы
- Выявляй боли и потребности
- Показывай что понимаешь
- НЕ спеши с решением
"""
            if analysis.get('question_to_ask'):
                instructions += f"\nМОЖЕШЬ СПРОСИТЬ: \"{analysis['question_to_ask']}\"\n"

        elif analysis['stage'] == 'deepening':
            instructions += """
ТВОЯ ЗАДАЧА НА ЭТОМ ЭТАПЕ:
- Углубляйся в проблему
- Проявляй эмпатию
- Дели личным опытом если уместно
- Готовь почву для решения
"""

        elif analysis['stage'] == 'solution_hint':
            instructions += """
ТВОЯ ЗАДАЧА НА ЭТОМ ЭТАПЕ:
- Плавно подводи к решению
- Не впаривай — заинтересовывай
- Расскажи свою историю / историю клиента
"""
            if analysis.get('solution_hint'):
                instructions += f"\nИСПОЛЬЗУЙ ПОДВОДКУ: \"{analysis['solution_hint']}\"\n"

        elif analysis['stage'] == 'solution':
            instructions += f"""
ТВОЯ ЗАДАЧА НА ЭТОМ ЭТАПЕ:
- ТЕПЕРЬ можно предложить решение!
- Конкретный продукт под боль: {analysis['pains']}
- Объясни КАК это поможет именно ему
- Дай конкретику (состав, результат, цена)
"""

        elif analysis['stage'] == 'objection':
            instructions += """
ТВОЯ ЗАДАЧА НА ЭТОМ ЭТАПЕ:
- Отработай возражение мягко
- Не спорь, а понимай
- Приведи факт или историю
- Предложи попробовать без обязательств
"""
            if analysis.get('objection_response'):
                instructions += f"\nСКРИПТ: {analysis['objection_response']}\n"

        elif analysis['stage'] == 'closing':
            instructions += """
ТВОЯ ЗАДАЧА НА ЭТОМ ЭТАПЕ:
- Подведи к действию
- Предложи следующий шаг (консультация, заказ)
- Сними последние сомнения
- Дай CTA со ссылкой на регистрацию
"""

        instructions += """
=== КОНЕЦ ИНСТРУКЦИЙ ===

ВАЖНО: Веди диалог ЕСТЕСТВЕННО. Не перескакивай этапы!
"""

        return instructions

    def reset_context(self, user_id: int):
        """Сбрасывает контекст пользователя"""
        if user_id in self._contexts:
            del self._contexts[user_id]
            logger.info(f"Reset conversation context for user {user_id}")


# Глобальный экземпляр воронки
_funnel_instance: Optional[ConversationalFunnel] = None


def get_conversational_funnel() -> ConversationalFunnel:
    """Получает глобальный экземпляр воронки"""
    global _funnel_instance
    if _funnel_instance is None:
        _funnel_instance = ConversationalFunnel()
    return _funnel_instance
