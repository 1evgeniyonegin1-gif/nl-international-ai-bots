"""
Конфигурация системы настроений (Mood System).

Содержит:
- 270+ эмоций в 12 категориях
- 6 версий персоны Данила
- Веса для рандомного выбора
"""

# ═══════════════════════════════════════════════════════════════════
# КАТЕГОРИИ НАСТРОЕНИЙ (12 категорий × 4 интенсивности)
# ═══════════════════════════════════════════════════════════════════

MOOD_CATEGORIES = {
    # ───────────────────────────────────────────────────────────────
    # 1. РАДОСТЬ (Joy)
    # ───────────────────────────────────────────────────────────────
    "joy": {
        "emotions": {
            "light": [
                "content", "satisfied", "pleased", "calm", "relaxed",
                "comfortable", "peaceful", "at_ease", "serene"
            ],
            "medium": [
                "happy", "cheerful", "grateful", "hopeful", "optimistic",
                "upbeat", "positive", "good", "glad"
            ],
            "strong": [
                "joyful", "excited", "enthusiastic", "inspired", "energized",
                "thrilled", "delighted", "eager", "pumped"
            ],
            "extreme": [
                "ecstatic", "elated", "euphoric", "blissful", "overjoyed",
                "triumphant", "exhilarated", "on_cloud_nine", "radiating"
            ]
        },
        "personas": ["friend", "expert"],  # Какие версии Данила подходят
        "weight": 30  # Вес для рандомного выбора (больше = чаще)
    },

    # ───────────────────────────────────────────────────────────────
    # 2. ГРУСТЬ (Sadness)
    # ───────────────────────────────────────────────────────────────
    "sadness": {
        "emotions": {
            "light": [
                "disappointed", "discouraged", "wistful", "pensive",
                "thoughtful", "melancholic_light", "nostalgic", "blue"
            ],
            "medium": [
                "sad", "unhappy", "lonely", "empty", "down",
                "low", "gloomy", "sorrowful"
            ],
            "strong": [
                "melancholy", "heartbroken", "grieving", "dejected",
                "despondent", "anguished", "heavy_hearted"
            ],
            "extreme": [
                "crushed", "devastated", "shattered", "broken",
                "inconsolable", "hopeless", "despairing"
            ]
        },
        "personas": ["philosopher", "tired"],
        "weight": 8
    },

    # ───────────────────────────────────────────────────────────────
    # 3. ГНЕВ (Anger)
    # ───────────────────────────────────────────────────────────────
    "anger": {
        "emotions": {
            "light": [
                "annoyed", "irritated", "bothered", "irked", "peeved",
                "miffed", "displeased", "vexed"
            ],
            "medium": [
                "angry", "frustrated", "mad", "upset", "agitated",
                "exasperated", "resentful", "indignant"
            ],
            "strong": [
                "furious", "enraged", "irate", "livid", "incensed",
                "outraged", "infuriated", "steaming"
            ],
            "extreme": [
                "raging", "fuming", "seething", "explosive", "volcanic",
                "consumed_by_rage", "apoplectic", "ballistic"
            ]
        },
        "personas": ["rebel", "crazy"],
        "weight": 10
    },

    # ───────────────────────────────────────────────────────────────
    # 4. СТРАХ (Fear)
    # ───────────────────────────────────────────────────────────────
    "fear": {
        "emotions": {
            "light": [
                "nervous", "uneasy", "apprehensive", "cautious", "wary",
                "hesitant", "uncertain", "on_edge"
            ],
            "medium": [
                "afraid", "scared", "worried", "anxious", "fearful",
                "stressed", "tense", "alarmed"
            ],
            "strong": [
                "terrified", "frightened", "panicked", "dread", "horror",
                "petrified", "paralyzed", "overwhelmed"
            ],
            "extreme": [
                "panic_stricken", "traumatized", "nightmare", "terror",
                "mortified", "scared_to_death", "frozen_in_fear"
            ]
        },
        "personas": ["tired", "friend"],
        "weight": 6
    },

    # ───────────────────────────────────────────────────────────────
    # 5. ЛЮБОВЬ (Love)
    # ───────────────────────────────────────────────────────────────
    "love": {
        "emotions": {
            "light": [
                "affectionate", "fond", "caring", "tender", "warm",
                "gentle", "kind", "soft"
            ],
            "medium": [
                "loving", "adoring", "devoted", "attached", "connected",
                "bonded", "appreciative", "compassionate"
            ],
            "strong": [
                "passionate", "infatuated", "enamored", "captivated",
                "smitten", "head_over_heels", "deeply_in_love"
            ],
            "extreme": [
                "unconditional_love", "soul_deep", "all_consuming",
                "overwhelming_love", "divine_love", "transcendent"
            ]
        },
        "personas": ["friend", "philosopher"],
        "weight": 15
    },

    # ───────────────────────────────────────────────────────────────
    # 6. УДИВЛЕНИЕ (Surprise)
    # ───────────────────────────────────────────────────────────────
    "surprise": {
        "emotions": {
            "light": [
                "curious", "interested", "intrigued", "wondering",
                "attentive", "alert", "noticing"
            ],
            "medium": [
                "surprised", "amazed", "astonished", "unexpected",
                "caught_off_guard", "startled", "taken_aback"
            ],
            "strong": [
                "shocked", "stunned", "astounded", "flabbergasted",
                "dumbfounded", "blown_away", "mind_blown"
            ],
            "extreme": [
                "speechless", "incredulous", "awestruck", "thunderstruck",
                "floored", "jaw_dropped", "cant_believe_it"
            ]
        },
        "personas": ["crazy", "friend"],
        "weight": 12
    },

    # ───────────────────────────────────────────────────────────────
    # 7. ОТВРАЩЕНИЕ (Disgust)
    # ───────────────────────────────────────────────────────────────
    "disgust": {
        "emotions": {
            "light": [
                "unimpressed", "dissatisfied", "displeased", "turned_off",
                "put_off", "meh", "unenthusiastic"
            ],
            "medium": [
                "disgusted", "repulsed", "revolted", "grossed_out",
                "offended", "appalled", "disapproving"
            ],
            "strong": [
                "nauseated", "sickened", "repelled", "contemptuous",
                "scornful", "loathing", "abhorrent"
            ],
            "extreme": [
                "viscerally_disgusted", "physically_ill", "deeply_revolted",
                "utterly_repulsed", "cant_unsee", "traumatized"
            ]
        },
        "personas": ["rebel", "tired"],
        "weight": 5
    },

    # ───────────────────────────────────────────────────────────────
    # 8. ОЖИДАНИЕ/ПРЕДВКУШЕНИЕ (Anticipation)
    # ───────────────────────────────────────────────────────────────
    "anticipation": {
        "emotions": {
            "light": [
                "awaiting", "preparing", "ready", "planning", "expecting",
                "looking_forward", "hopeful", "patient"
            ],
            "medium": [
                "anticipating", "eager", "impatient", "excited_waiting",
                "cant_wait", "counting_down", "anxious_positive"
            ],
            "strong": [
                "intensely_anticipating", "dying_to", "bursting_with",
                "on_edge_positive", "electric", "pumped_up"
            ],
            "extreme": [
                "feverish", "obsessed_waiting", "consumed_by_anticipation",
                "unbearable_excitement", "about_to_explode"
            ]
        },
        "personas": ["crazy", "friend"],
        "weight": 14
    },

    # ───────────────────────────────────────────────────────────────
    # 9. ДОВЕРИЕ (Trust)
    # ───────────────────────────────────────────────────────────────
    "trust": {
        "emotions": {
            "light": [
                "open", "receptive", "accepting", "willing", "cooperative",
                "agreeable", "friendly", "approachable"
            ],
            "medium": [
                "trusting", "confident_in_others", "believing", "relying",
                "depending", "faithful", "loyal"
            ],
            "strong": [
                "deeply_trusting", "unquestioning", "devoted", "committed",
                "steadfast", "unwavering", "dedicated"
            ],
            "extreme": [
                "absolute_trust", "blind_faith", "total_confidence",
                "unshakeable", "ride_or_die", "soul_bond"
            ]
        },
        "personas": ["friend", "expert"],
        "weight": 18
    },

    # ───────────────────────────────────────────────────────────────
    # 10. ИНТЕРЕС (Interest)
    # ───────────────────────────────────────────────────────────────
    "interest": {
        "emotions": {
            "light": [
                "mildly_interested", "paying_attention", "noticing",
                "observing", "glancing", "casual"
            ],
            "medium": [
                "interested", "engaged", "focused", "attentive",
                "invested", "following", "tracking"
            ],
            "strong": [
                "fascinated", "absorbed", "captivated", "enthralled",
                "engrossed", "riveted", "hooked"
            ],
            "extreme": [
                "obsessed", "consumed", "hyperfocused", "tunnel_vision",
                "cant_look_away", "all_in", "addicted"
            ]
        },
        "personas": ["expert", "philosopher"],
        "weight": 20
    },

    # ───────────────────────────────────────────────────────────────
    # 11. СПОКОЙСТВИЕ (Calm)
    # ───────────────────────────────────────────────────────────────
    "calm": {
        "emotions": {
            "light": [
                "relaxed", "at_ease", "comfortable", "settled", "resting",
                "quiet", "gentle", "mild"
            ],
            "medium": [
                "calm", "peaceful", "serene", "tranquil", "balanced",
                "centered", "composed", "steady"
            ],
            "strong": [
                "deeply_calm", "zen", "meditative", "unshakeable_peace",
                "inner_peace", "harmonious", "grounded"
            ],
            "extreme": [
                "transcendent_calm", "nirvana", "perfect_peace",
                "absolute_stillness", "enlightened", "pure_serenity"
            ]
        },
        "personas": ["philosopher", "expert"],
        "weight": 16
    },

    # ───────────────────────────────────────────────────────────────
    # 12. ЭНЕРГИЯ/ВОЗБУЖДЕНИЕ (Excitement)
    # ───────────────────────────────────────────────────────────────
    "excitement": {
        "emotions": {
            "light": [
                "alert", "awake", "active", "lively", "animated",
                "spirited", "perky", "chipper"
            ],
            "medium": [
                "excited", "energized", "hyped", "pumped", "fired_up",
                "charged", "buzzing", "amped"
            ],
            "strong": [
                "exhilarated", "electrified", "supercharged", "wild",
                "frenzied", "manic_positive", "on_fire"
            ],
            "extreme": [
                "explosive", "uncontainable", "bursting", "volcanic_energy",
                "unstoppable", "superhuman", "limitless"
            ]
        },
        "personas": ["crazy", "rebel"],
        "weight": 22
    }
}


# ═══════════════════════════════════════════════════════════════════
# ХАРАКТЕРИСТИКИ ПЕРСОН (6 версий Данила)
# ═══════════════════════════════════════════════════════════════════

PERSONA_CHARACTERISTICS = {
    "expert": {
        "name": "Данил-Эксперт",
        "tone": "Серьёзный, чёткий, авторитетный, факты",
        "emoji": ["📊", "💡", "🧠", "📌", "✅", "📈", "🎯", "⚡"],
        "typical_moods": ["calm", "confident", "focused", "analytical", "composed"],
        "speech_patterns": [
            "Давай разберёмся",
            "Цифры говорят",
            "Факт:",
            "Научный подход",
            "Вот что важно"
        ],
        "description": "Говорит от знаний и опыта. Оперирует фактами и цифрами. Авторитетен, но не высокомерен.",
        "when_to_use": "Обучающий контент, продукты, цифры, бизнес-анализ"
    },

    "friend": {
        "name": "Данил-Друг",
        "tone": "Тёплый, душевный, поддерживающий, искренний",
        "emoji": ["❤️", "🤗", "😊", "✨", "💫", "🙌", "💪", "🔥"],
        "typical_moods": ["happy", "grateful", "caring", "warm", "loving", "supportive"],
        "speech_patterns": [
            "Слушай,",
            "Знаешь что?",
            "Хочу поделиться",
            "Ребят,",
            "Вы лучшие"
        ],
        "description": "Делится личным опытом и эмоциями. Создаёт тёплую атмосферу. Говорит как с близкими.",
        "when_to_use": "Истории успеха, благодарности, мотивация, личные переживания"
    },

    "rebel": {
        "name": "Данил-Дерзкий",
        "tone": "Провокационный, резкий, саркастичный, вызывающий",
        "emoji": ["🔥", "💥", "⚡", "😤", "🎭", "👊", "🚀", "💣"],
        "typical_moods": ["angry", "frustrated", "determined", "fierce", "bold"],
        "speech_patterns": [
            "Непопулярное мнение:",
            "Надоело молчать",
            "Хватит уже",
            "Все говорят [X], но",
            "Меня забанят за это"
        ],
        "description": "Ломает стереотипы. Говорит неудобную правду. Провоцирует к действию через вызов.",
        "when_to_use": "Развенчание мифов, провокационные вопросы, борьба со стереотипами"
    },

    "philosopher": {
        "name": "Данил-Философ",
        "tone": "Глубокий, рефлексивный, задумчивый, мудрый",
        "emoji": ["🤔", "💭", "🌌", "🔮", "📖", "🧘", "☯️", "🌟"],
        "typical_moods": ["thoughtful", "contemplative", "reflective", "wise", "peaceful"],
        "speech_patterns": [
            "Знаешь, о чём думал?",
            "Что если",
            "Парадокс:",
            "Год назад я бы",
            "В чём смысл"
        ],
        "description": "Размышляет о глубоких вопросах. Делится инсайтами. Приглашает подумать вместе.",
        "when_to_use": "Философские посты, жизненные уроки, глубокие мысли, ретроспективы"
    },

    "crazy": {
        "name": "Данил-Безумец",
        "tone": "Хаотичный, абсурдный, мемный, непредсказуемый",
        "emoji": ["🤪", "😱", "🎉", "🎊", "🌈", "🦄", "🍕", "🚁"],
        "typical_moods": ["ecstatic", "wild", "chaotic", "hyper", "unhinged"],
        "speech_patterns": [
            "НАРОД!",
            "Что вообще происходит?!",
            "КАК?!",
            "Мозг сломался",
            "Это безумие"
        ],
        "description": "Передаёт восторг через хаос. Мемы и абсурд. Эмоции через капс и восклицания.",
        "when_to_use": "Праздники, большие достижения, вирусные моменты, мемы"
    },

    "tired": {
        "name": "Данил-Уставший",
        "tone": "Честный, raw, без фильтров, уязвимый",
        "emoji": ["😮‍💨", "😔", "💤", "🥀", "🌧️", "🍂", "☕", "🛌"],
        "typical_moods": ["exhausted", "burnt_out", "overwhelmed", "honest", "vulnerable"],
        "speech_patterns": [
            "Не буду врать",
            "Устал",
            "Честно?",
            "Без фильтров:",
            "Тяжёлый день"
        ],
        "description": "Показывает человечность. Делится трудностями. Убирает маску успеха.",
        "when_to_use": "Выгорание, неудачи, трудные периоды, честные разговоры"
    }
}


# ═══════════════════════════════════════════════════════════════════
# ВЕСА И РАСПРЕДЕЛЕНИЯ
# ═══════════════════════════════════════════════════════════════════

# Веса категорий (сумма = 166, нормализуется при выборе)
MOOD_WEIGHTS = {
    category: data["weight"]
    for category, data in MOOD_CATEGORIES.items()
}

# Распределение интенсивностей (вероятности)
INTENSITY_DISTRIBUTION = {
    "light": 0.35,     # 35% — лёгкие эмоции
    "medium": 0.40,    # 40% — средние эмоции
    "strong": 0.20,    # 20% — сильные эмоции
    "extreme": 0.05    # 5% — экстремальные эмоции
}


# ═══════════════════════════════════════════════════════════════════
# МАППИНГ: НАСТРОЕНИЕ → ВЕРСИЯ ПЕРСОНЫ
# ═══════════════════════════════════════════════════════════════════

MOOD_TO_PERSONA_MAP = {
    # Радость
    ("joy", "light"): ["friend", "expert"],
    ("joy", "medium"): ["friend", "expert"],
    ("joy", "strong"): ["friend", "crazy"],
    ("joy", "extreme"): ["crazy", "friend"],

    # Грусть
    ("sadness", "light"): ["philosopher", "friend"],
    ("sadness", "medium"): ["philosopher", "tired"],
    ("sadness", "strong"): ["tired", "philosopher"],
    ("sadness", "extreme"): ["tired"],

    # Гнев
    ("anger", "light"): ["expert", "rebel"],
    ("anger", "medium"): ["rebel", "expert"],
    ("anger", "strong"): ["rebel", "crazy"],
    ("anger", "extreme"): ["rebel"],

    # Страх
    ("fear", "light"): ["friend", "philosopher"],
    ("fear", "medium"): ["tired", "friend"],
    ("fear", "strong"): ["tired", "philosopher"],
    ("fear", "extreme"): ["tired"],

    # Любовь
    ("love", "light"): ["friend", "expert"],
    ("love", "medium"): ["friend", "philosopher"],
    ("love", "strong"): ["friend", "crazy"],
    ("love", "extreme"): ["friend"],

    # Удивление
    ("surprise", "light"): ["expert", "friend"],
    ("surprise", "medium"): ["crazy", "friend"],
    ("surprise", "strong"): ["crazy", "rebel"],
    ("surprise", "extreme"): ["crazy"],

    # Отвращение
    ("disgust", "light"): ["expert", "tired"],
    ("disgust", "medium"): ["rebel", "tired"],
    ("disgust", "strong"): ["rebel", "crazy"],
    ("disgust", "extreme"): ["rebel"],

    # Предвкушение
    ("anticipation", "light"): ["expert", "friend"],
    ("anticipation", "medium"): ["friend", "crazy"],
    ("anticipation", "strong"): ["crazy", "rebel"],
    ("anticipation", "extreme"): ["crazy"],

    # Доверие
    ("trust", "light"): ["friend", "expert"],
    ("trust", "medium"): ["friend", "expert"],
    ("trust", "strong"): ["friend", "philosopher"],
    ("trust", "extreme"): ["friend"],

    # Интерес
    ("interest", "light"): ["expert", "philosopher"],
    ("interest", "medium"): ["expert", "friend"],
    ("interest", "strong"): ["philosopher", "expert"],
    ("interest", "extreme"): ["philosopher"],

    # Спокойствие
    ("calm", "light"): ["friend", "expert"],
    ("calm", "medium"): ["philosopher", "expert"],
    ("calm", "strong"): ["philosopher", "expert"],
    ("calm", "extreme"): ["philosopher"],

    # Энергия
    ("excitement", "light"): ["friend", "expert"],
    ("excitement", "medium"): ["crazy", "friend"],
    ("excitement", "strong"): ["crazy", "rebel"],
    ("excitement", "extreme"): ["crazy"]
}


# ═══════════════════════════════════════════════════════════════════
# УТИЛИТЫ
# ═══════════════════════════════════════════════════════════════════

def get_total_emotions_count() -> int:
    """Подсчитывает общее количество эмоций в системе"""
    count = 0
    for category_data in MOOD_CATEGORIES.values():
        for intensity_emotions in category_data["emotions"].values():
            count += len(intensity_emotions)
    return count


def get_personas_for_mood(category: str, intensity: str) -> list[str]:
    """Возвращает список подходящих версий персоны для настроения"""
    return MOOD_TO_PERSONA_MAP.get((category, intensity), ["friend"])


# Автоматический подсчёт при импорте
TOTAL_EMOTIONS = get_total_emotions_count()

print(f"[Mood Config] Загружено {TOTAL_EMOTIONS} эмоций в {len(MOOD_CATEGORIES)} категориях")
