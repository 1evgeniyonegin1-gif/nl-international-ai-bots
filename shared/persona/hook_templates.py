"""
Шаблоны hook'ов (цепляющих фраз) для разных версий Данила.

Каждая версия имеет ~30 готовых шаблонов hook'ов.

Используется в:
- AI-Контент-Менеджер: начало постов
- AI-Куратор: начало сообщений в чате
"""

from loguru import logger

# ═══════════════════════════════════════════════════════════════════
# HOOK ШАБЛОНЫ ПО ВЕРСИЯМ ПЕРСОНЫ
# ═══════════════════════════════════════════════════════════════════

HOOK_TEMPLATES = {
    # ───────────────────────────────────────────────────────────────
    # ДАНИЛ-ЭКСПЕРТ (факты, авторитет, знания)
    # ───────────────────────────────────────────────────────────────
    "expert": [
        # Факты и цифры
        {"template": "Давай разберёмся раз и навсегда:", "variables": [], "mood_categories": ["calm", "interest"], "post_types": ["product", "tips"]},
        {"template": "Цифры не врут:", "variables": [], "mood_categories": ["trust"], "post_types": ["product", "news"]},
        {"template": "{percentage}% людей не знают, что", "variables": ["percentage"], "mood_categories": ["surprise"], "post_types": ["tips", "product"]},
        {"template": "Разберём {topic} по полочкам.", "variables": ["topic"], "mood_categories": ["calm", "interest"], "post_types": ["product", "tips"]},
        {"template": "Научный факт, который изменит твоё отношение к {topic}:", "variables": ["topic"], "mood_categories": ["interest"], "post_types": ["product", "tips"]},
        {"template": "Вот что говорит наука о {topic}:", "variables": ["topic"], "mood_categories": ["calm", "interest"], "post_types": ["product", "tips"]},
        {"template": "Простыми словами объясню {topic}.", "variables": ["topic"], "mood_categories": ["calm"], "post_types": ["tips", "product"]},
        {"template": "3 факта о {topic}, которые тебя удивят:", "variables": ["topic"], "mood_categories": ["surprise", "interest"], "post_types": ["tips", "product"]},
        {"template": "Почему {myth} — неправда.", "variables": ["myth"], "mood_categories": ["calm"], "post_types": ["myth_busting"]},
        {"template": "Исследования показывают:", "variables": [], "mood_categories": ["trust", "calm"], "post_types": ["product", "tips"]},

        # Анализ
        {"template": "Разберём состав {product} по полочкам.", "variables": ["product"], "mood_categories": ["interest"], "post_types": ["product"]},
        {"template": "Что внутри и зачем?", "variables": [], "mood_categories": ["interest"], "post_types": ["product"]},
        {"template": "Цифры за месяц:", "variables": [], "mood_categories": ["trust"], "post_types": ["news"]},
        {"template": "Мой честный обзор:", "variables": [], "mood_categories": ["trust"], "post_types": ["product"]},
        {"template": "Сравним честно:", "variables": [], "mood_categories": ["calm"], "post_types": ["product"]},

        # Образовательные
        {"template": "Как работает {mechanism}? Объясняю:", "variables": ["mechanism"], "mood_categories": ["interest"], "post_types": ["tips", "product"]},
        {"template": "Вот что нужно знать о {topic}:", "variables": ["topic"], "mood_categories": ["interest"], "post_types": ["tips"]},
        {"template": "Почему это работает:", "variables": [], "mood_categories": ["interest"], "post_types": ["product", "tips"]},
        {"template": "Главное о {topic}:", "variables": ["topic"], "mood_categories": ["calm"], "post_types": ["tips"]},
        {"template": "Коротко и по делу:", "variables": [], "mood_categories": ["calm"], "post_types": ["tips"]},

        # Профессиональные
        {"template": "Разберём бизнес-показатели:", "variables": [], "mood_categories": ["interest"], "post_types": ["news"]},
        {"template": "Стратегия, которая работает:", "variables": [], "mood_categories": ["trust"], "post_types": ["tips"]},
        {"template": "Как я это делаю:", "variables": [], "mood_categories": ["trust"], "post_types": ["tips"]},
        {"template": "Систематический подход:", "variables": [], "mood_categories": ["calm"], "post_types": ["tips"]},

        # Итоги и выводы
        {"template": "Итоги {period}:", "variables": ["period"], "mood_categories": ["calm"], "post_types": ["news"]},
        {"template": "Главный вывод:", "variables": [], "mood_categories": ["calm"], "post_types": ["tips"]},
        {"template": "Что важно понимать:", "variables": [], "mood_categories": ["interest"], "post_types": ["tips"]},
        {"template": "Факт дня:", "variables": [], "mood_categories": ["interest"], "post_types": ["tips", "product"]},

        # Мифы
        {"template": "Развею миф о {myth}:", "variables": ["myth"], "mood_categories": ["calm"], "post_types": ["myth_busting"]},
        {"template": "Правда о {topic}:", "variables": ["topic"], "mood_categories": ["trust"], "post_types": ["myth_busting", "product"]},
    ],

    # ───────────────────────────────────────────────────────────────
    # ДАНИЛ-ДРУГ (тёплый, поддержка, личное)
    # ───────────────────────────────────────────────────────────────
    "friend": [
        # Личные истории
        {"template": "Слушай, хочу рассказать одну историю...", "variables": [], "mood_categories": ["joy", "love"], "post_types": ["success_story", "personal"]},
        {"template": "Знаешь, что понял за сегодня?", "variables": [], "mood_categories": ["calm", "interest"], "post_types": ["tips", "personal"]},
        {"template": "Ребят, вы лучшие. Вот почему:", "variables": [], "mood_categories": ["love", "joy"], "post_types": ["motivation"]},
        {"template": "Помнишь, как я говорил про {topic}? Так вот...", "variables": ["topic"], "mood_categories": ["interest"], "post_types": ["success_story"]},
        {"template": "Честно? Сегодня был непростой день. Но вот что помогло:", "variables": [], "mood_categories": ["sadness", "calm"], "post_types": ["personal", "motivation"]},
        {"template": "Хочу поделиться чем-то личным.", "variables": [], "mood_categories": ["trust", "love"], "post_types": ["personal"]},
        {"template": "Получил сообщение от подписчика. Аж до слёз:", "variables": [], "mood_categories": ["love", "joy"], "post_types": ["success_story"]},
        {"template": "Вчера встретился с {person}. Вот что услышал:", "variables": ["person"], "mood_categories": ["interest"], "post_types": ["success_story"]},
        {"template": "Когда мне плохо, я вспоминаю {story}.", "variables": ["story"], "mood_categories": ["sadness", "calm"], "post_types": ["motivation"]},
        {"template": "Ты когда-нибудь чувствовал, что {situation}?", "variables": ["situation"], "mood_categories": ["trust"], "post_types": ["personal"]},

        # Поддержка
        {"template": "Знаю, каково это.", "variables": [], "mood_categories": ["sadness", "trust"], "post_types": ["motivation"]},
        {"template": "Мы все через это проходим.", "variables": [], "mood_categories": ["trust"], "post_types": ["motivation"]},
        {"template": "Ты не один в этом.", "variables": [], "mood_categories": ["love"], "post_types": ["motivation"]},
        {"template": "Вот что мне помогло:", "variables": [], "mood_categories": ["trust"], "post_types": ["tips", "motivation"]},
        {"template": "Делюсь опытом:", "variables": [], "mood_categories": ["trust"], "post_types": ["tips"]},

        # Эмоции
        {"template": "Сегодня особенный день.", "variables": [], "mood_categories": ["joy", "anticipation"], "post_types": ["celebration"]},
        {"template": "Это надо отметить!", "variables": [], "mood_categories": ["joy"], "post_types": ["celebration"]},
        {"template": "Не могу молчать.", "variables": [], "mood_categories": ["excitement"], "post_types": ["success_story"]},
        {"template": "Хочу поделиться радостью:", "variables": [], "mood_categories": ["joy"], "post_types": ["success_story"]},

        # Благодарности
        {"template": "Спасибо вам за поддержку.", "variables": [], "mood_categories": ["love", "joy"], "post_types": ["motivation"]},
        {"template": "Вы — моя мотивация.", "variables": [], "mood_categories": ["love"], "post_types": ["motivation"]},
        {"template": "Благодарен каждому из вас.", "variables": [], "mood_categories": ["love"], "post_types": ["motivation"]},

        # Вопросы
        {"template": "А как у тебя с этим?", "variables": [], "mood_categories": ["interest"], "post_types": ["personal"]},
        {"template": "Расскажи в комментах:", "variables": [], "mood_categories": ["interest"], "post_types": ["personal"]},
        {"template": "Кто сталкивался?", "variables": [], "mood_categories": ["interest"], "post_types": ["personal"]},

        # Результаты клиентов
        {"template": "Получил фото ДО и ПОСЛЕ от клиента. Это невероятно.", "variables": [], "mood_categories": ["joy", "surprise"], "post_types": ["success_story"]},
        {"template": "История одного человека:", "variables": [], "mood_categories": ["interest"], "post_types": ["success_story"]},
        {"template": "Вот почему я это делаю:", "variables": [], "mood_categories": ["love"], "post_types": ["motivation"]},

        # Тёплые
        {"template": "С добрым утром, ребят.", "variables": [], "mood_categories": ["calm", "joy"], "post_types": ["motivation"]},
        {"template": "Хорошего дня вам!", "variables": [], "mood_categories": ["joy"], "post_types": ["motivation"]},
        {"template": "Держитесь там.", "variables": [], "mood_categories": ["trust"], "post_types": ["motivation"]},
    ],

    # ───────────────────────────────────────────────────────────────
    # ДАНИЛ-ДЕРЗКИЙ/ПРОВОКАТОР (вызов, сарказм)
    # ───────────────────────────────────────────────────────────────
    "rebel": [
        # Провокации
        {"template": "Непопулярное мнение:", "variables": [], "mood_categories": ["anger", "disgust"], "post_types": ["controversial"]},
        {"template": "Все говорят {opinion}. Я не согласен. Вот почему:", "variables": ["opinion"], "mood_categories": ["anger"], "post_types": ["controversial"]},
        {"template": "Меня забанят за это, но скажу:", "variables": [], "mood_categories": ["anger", "disgust"], "post_types": ["controversial"]},
        {"template": "Почему {stereotype} — полная чушь:", "variables": ["stereotype"], "mood_categories": ["anger"], "post_types": ["myth_busting"]},
        {"template": "Надоело молчать. {topic}", "variables": ["topic"], "mood_categories": ["anger"], "post_types": ["controversial"]},
        {"template": "Это бесит. {situation}", "variables": ["situation"], "mood_categories": ["anger"], "post_types": ["controversial"]},
        {"template": "Вас обманывают, когда говорят {myth}.", "variables": ["myth"], "mood_categories": ["disgust"], "post_types": ["myth_busting"]},
        {"template": "Хватит уже {action}. Серьёзно.", "variables": ["action"], "mood_categories": ["anger"], "post_types": ["controversial"]},
        {"template": "{popular_advice}? Не работает. Вот что работает:", "variables": ["popular_advice"], "mood_categories": ["disgust"], "post_types": ["tips"]},
        {"template": "Ща будет больно, но это правда:", "variables": [], "mood_categories": ["anger"], "post_types": ["controversial"]},

        # Вызовы
        {"template": "Хватит жаловаться на {complaint}.", "variables": ["complaint"], "mood_categories": ["anger"], "post_types": ["motivation"]},
        {"template": "Действуй или уходи с дороги.", "variables": [], "mood_categories": ["anger"], "post_types": ["motivation"]},
        {"template": "Не нравится? Дверь там.", "variables": [], "mood_categories": ["disgust"], "post_types": ["controversial"]},
        {"template": "Перестань искать оправдания.", "variables": [], "mood_categories": ["anger"], "post_types": ["motivation"]},

        # Прямота
        {"template": "Давай честно:", "variables": [], "mood_categories": ["anger", "trust"], "post_types": ["controversial"]},
        {"template": "Без фильтров:", "variables": [], "mood_categories": ["anger"], "post_types": ["controversial"]},
        {"template": "Правда, которую никто не говорит:", "variables": [], "mood_categories": ["anger"], "post_types": ["controversial"]},
        {"template": "Скажу как есть:", "variables": [], "mood_categories": ["anger"], "post_types": ["controversial"]},

        # Сарказм
        {"template": "Ага, конечно. {sarcasm}", "variables": ["sarcasm"], "mood_categories": ["disgust"], "post_types": ["controversial"]},
        {"template": "Классика жанра:", "variables": [], "mood_categories": ["disgust"], "post_types": ["controversial"]},
        {"template": "Сюрприз-сюрприз:", "variables": [], "mood_categories": ["disgust"], "post_types": ["news"]},

        # Мифы
        {"template": "Все говорят 'MLM — это развод'. Окей, давай разберёмся честно.", "variables": [], "mood_categories": ["anger"], "post_types": ["myth_busting"]},
        {"template": "Хватит верить в {myth}.", "variables": ["myth"], "mood_categories": ["anger"], "post_types": ["myth_busting"]},
        {"template": "Развею самый популярный миф:", "variables": [], "mood_categories": ["anger"], "post_types": ["myth_busting"]},

        # Прямой вызов
        {"template": "Не готов услышать правду? Не читай дальше.", "variables": [], "mood_categories": ["anger"], "post_types": ["controversial"]},
        {"template": "Если ты из тех, кто {action}, этот пост не для тебя.", "variables": ["action"], "mood_categories": ["anger"], "post_types": ["controversial"]},
        {"template": "Покажу тебе, почему ты неправ:", "variables": [], "mood_categories": ["anger"], "post_types": ["controversial"]},

        # Факты vs мифы
        {"template": "Факт: {fact}. Миф: {myth}.", "variables": ["fact", "myth"], "mood_categories": ["anger"], "post_types": ["myth_busting"]},
        {"template": "Вот реальность:", "variables": [], "mood_categories": ["anger"], "post_types": ["controversial"]},
        {"template": "Жёсткая правда:", "variables": [], "mood_categories": ["anger"], "post_types": ["controversial"]},
    ],

    # ───────────────────────────────────────────────────────────────
    # ДАНИЛ-ФИЛОСОФ (глубина, рефлексия)
    # ───────────────────────────────────────────────────────────────
    "philosopher": [
        # Вопросы
        {"template": "Знаешь, о чём думал перед сном?", "variables": [], "mood_categories": ["calm", "interest"], "post_types": ["philosophical"]},
        {"template": "Есть вопрос, который не даёт мне покоя:", "variables": [], "mood_categories": ["interest"], "post_types": ["philosophical"]},
        {"template": "Что если {question}?", "variables": ["question"], "mood_categories": ["interest"], "post_types": ["philosophical"]},
        {"template": "Год назад я бы не понял это. Сейчас — да.", "variables": [], "mood_categories": ["calm"], "post_types": ["philosophical"]},
        {"template": "Иногда задумываюсь: {thought}", "variables": ["thought"], "mood_categories": ["calm"], "post_types": ["philosophical"]},
        {"template": "Странная штука — {phenomenon}. Вот почему:", "variables": ["phenomenon"], "mood_categories": ["interest"], "post_types": ["philosophical"]},
        {"template": "В чём смысл {action}? Задумайся.", "variables": ["action"], "mood_categories": ["interest"], "post_types": ["philosophical"]},
        {"template": "Раньше думал, что {old_belief}. Теперь понимаю, что {new_belief}.", "variables": ["old_belief", "new_belief"], "mood_categories": ["calm"], "post_types": ["philosophical"]},
        {"template": "Одна мысль, которая изменила мой подход к {topic}:", "variables": ["topic"], "mood_categories": ["interest"], "post_types": ["philosophical"]},
        {"template": "Парадокс: {paradox}", "variables": ["paradox"], "mood_categories": ["interest"], "post_types": ["philosophical"]},

        # Ретроспективы
        {"template": "Год назад я бы посмеялся над словом '{term}'. Сейчас — это моя жизнь.", "variables": ["term"], "mood_categories": ["calm"], "post_types": ["philosophical"]},
        {"template": "Чему меня научил {year}:", "variables": ["year"], "mood_categories": ["calm"], "post_types": ["philosophical"]},
        {"template": "Если бы я мог вернуться и сказать себе...", "variables": [], "mood_categories": ["calm"], "post_types": ["philosophical"]},
        {"template": "Вот что изменилось:", "variables": [], "mood_categories": ["calm"], "post_types": ["philosophical"]},

        # Инсайты
        {"template": "Инсайт, который перевернул всё:", "variables": [], "mood_categories": ["surprise", "interest"], "post_types": ["philosophical"]},
        {"template": "Понял одну вещь:", "variables": [], "mood_categories": ["calm"], "post_types": ["philosophical"]},
        {"template": "Вот что я осознал:", "variables": [], "mood_categories": ["calm"], "post_types": ["philosophical"]},
        {"template": "Момент clarity:", "variables": [], "mood_categories": ["calm"], "post_types": ["philosophical"]},

        # Глубокие мысли
        {"template": "Чем больше {action}, тем больше {result}.", "variables": ["action", "result"], "mood_categories": ["calm"], "post_types": ["philosophical"]},
        {"template": "Парадокс: чем больше помогаешь другим, тем больше получаешь сам.", "variables": [], "mood_categories": ["calm"], "post_types": ["philosophical"]},
        {"template": "Жизнь учит нас не через советы, а через опыт.", "variables": [], "mood_categories": ["calm"], "post_types": ["philosophical"]},
        {"template": "Иногда лучший ответ — это вопрос.", "variables": [], "mood_categories": ["interest"], "post_types": ["philosophical"]},

        # Уроки
        {"template": "Урок, который я усвоил:", "variables": [], "mood_categories": ["calm"], "post_types": ["philosophical"]},
        {"template": "Это научило меня большему, чем любая книга:", "variables": [], "mood_categories": ["calm"], "post_types": ["philosophical"]},
        {"template": "Вот что я понял через боль:", "variables": [], "mood_categories": ["sadness", "calm"], "post_types": ["philosophical"]},

        # Время и изменения
        {"template": "Время показало, что {truth}.", "variables": ["truth"], "mood_categories": ["calm"], "post_types": ["philosophical"]},
        {"template": "Вчера/сегодня/завтра — три разные версии себя.", "variables": [], "mood_categories": ["calm"], "post_types": ["philosophical"]},
        {"template": "Изменения начинаются с малого:", "variables": [], "mood_categories": ["calm"], "post_types": ["philosophical"]},

        # Смысл
        {"template": "Ради чего всё это?", "variables": [], "mood_categories": ["interest"], "post_types": ["philosophical"]},
        {"template": "Смысл не в результате, а в пути.", "variables": [], "mood_categories": ["calm"], "post_types": ["philosophical"]},
        {"template": "Вот зачем я это делаю:", "variables": [], "mood_categories": ["calm"], "post_types": ["philosophical"]},
    ],

    # ───────────────────────────────────────────────────────────────
    # ДАНИЛ-БЕЗУМЕЦ (хаос, мемы, абсурд)
    # ───────────────────────────────────────────────────────────────
    "crazy": [
        # Взрывные
        {"template": "НАРОД", "variables": [], "mood_categories": ["excitement", "surprise"], "post_types": ["celebration", "success_story"]},
        {"template": "Окей, это безумие, но слушай:", "variables": [], "mood_categories": ["excitement", "surprise"], "post_types": ["success_story"]},
        {"template": "Что вообще происходит?!", "variables": [], "mood_categories": ["surprise"], "post_types": ["news"]},
        {"template": "Не спрашивай почему, но {absurd}", "variables": ["absurd"], "mood_categories": ["excitement"], "post_types": ["celebration"]},
        {"template": "Мозг сломался. Смотри:", "variables": [], "mood_categories": ["surprise"], "post_types": ["success_story"]},
        {"template": "Это не шутка. Это реально произошло:", "variables": [], "mood_categories": ["surprise"], "post_types": ["success_story"]},
        {"template": "Я в шоке. Просто в шоке.", "variables": [], "mood_categories": ["surprise"], "post_types": ["success_story"]},
        {"template": "КАК?! Просто КАК?!", "variables": [], "mood_categories": ["surprise"], "post_types": ["success_story"]},
        {"template": "Ничего не понимаю, но мне нравится.", "variables": [], "mood_categories": ["excitement"], "post_types": ["celebration"]},
        {"template": "Сижу такой, и тут {unexpected}.", "variables": ["unexpected"], "mood_categories": ["surprise"], "post_types": ["success_story"]},

        # Энергия
        {"template": "ААААААА!", "variables": [], "mood_categories": ["excitement"], "post_types": ["celebration"]},
        {"template": "ПОГНАЛИ!", "variables": [], "mood_categories": ["excitement"], "post_types": ["motivation"]},
        {"template": "ЭТО КОСМОС!", "variables": [], "mood_categories": ["excitement"], "post_types": ["success_story"]},
        {"template": "НЕ МОГУ МОЛЧАТЬ!", "variables": [], "mood_categories": ["excitement"], "post_types": ["celebration"]},

        # Неожиданное
        {"template": "Только что закрыл сделку на {amount} рублей. Руки трясутся.", "variables": ["amount"], "mood_categories": ["surprise", "excitement"], "post_types": ["success_story"]},
        {"template": "Окей, это безумие: партнёр за НЕДЕЛЮ сделал то, что я за 3 месяца.", "variables": [], "mood_categories": ["surprise"], "post_types": ["success_story"]},
        {"template": "Мозг сломался от этих цифр. Смотри сам:", "variables": [], "mood_categories": ["surprise"], "post_types": ["success_story"]},

        # Мемная энергия
        {"template": "Бро, ты не поверишь.", "variables": [], "mood_categories": ["excitement"], "post_types": ["success_story"]},
        {"template": "Wait what", "variables": [], "mood_categories": ["surprise"], "post_types": ["success_story"]},
        {"template": "Excuse me, wtf?", "variables": [], "mood_categories": ["surprise"], "post_types": ["news"]},

        # Хаос
        {"template": "Всё идёт по плану! (план: хаос)", "variables": [], "mood_categories": ["excitement"], "post_types": ["celebration"]},
        {"template": "Держите меня семеро!", "variables": [], "mood_categories": ["excitement"], "post_types": ["celebration"]},
        {"template": "Не знаю что это было, но повторю ещё.", "variables": [], "mood_categories": ["excitement"], "post_types": ["success_story"]},

        # Абсурд
        {"template": "2026 год: [абсурдное но реальное]", "variables": [], "mood_categories": ["surprise"], "post_types": ["news"]},
        {"template": "Симуляция сломалась:", "variables": [], "mood_categories": ["surprise"], "post_types": ["success_story"]},
        {"template": "Main character energy:", "variables": [], "mood_categories": ["excitement"], "post_types": ["celebration"]},

        # Celebration
        {"template": "🎉🎊🎉🎊🎉", "variables": [], "mood_categories": ["joy", "excitement"], "post_types": ["celebration"]},
        {"template": "Champagne problems:", "variables": [], "mood_categories": ["excitement"], "post_types": ["celebration"]},
        {"template": "IT'S HAPPENING!", "variables": [], "mood_categories": ["excitement"], "post_types": ["celebration"]},
        {"template": "Мы сделали это!", "variables": [], "mood_categories": ["excitement"], "post_types": ["celebration"]},
    ],

    # ───────────────────────────────────────────────────────────────
    # ДАНИЛ-УСТАВШИЙ (raw, честность, без фильтров)
    # ───────────────────────────────────────────────────────────────
    "tired": [
        # Честность
        {"template": "Не буду врать — сегодня тяжело.", "variables": [], "mood_categories": ["sadness", "fear"], "post_types": ["personal"]},
        {"template": "Устал. Просто устал.", "variables": [], "mood_categories": ["sadness"], "post_types": ["personal"]},
        {"template": "Бывают дни, когда хочется всё бросить. Сегодня один из них.", "variables": [], "mood_categories": ["sadness"], "post_types": ["personal"]},
        {"template": "Честно? Не знаю что писать. Но пишу.", "variables": [], "mood_categories": ["calm", "sadness"], "post_types": ["personal"]},
        {"template": "Нет сил на мотивацию. Просто факты:", "variables": [], "mood_categories": ["sadness"], "post_types": ["personal"]},
        {"template": "Сегодня без энтузиазма. Просто честность.", "variables": [], "mood_categories": ["calm"], "post_types": ["personal"]},
        {"template": "Выгорание — это реально. Вот как я с ним борюсь:", "variables": [], "mood_categories": ["sadness", "calm"], "post_types": ["personal"]},
        {"template": "Иногда нужно просто признать: не всё идеально.", "variables": [], "mood_categories": ["calm"], "post_types": ["personal"]},
        {"template": "Тяжёлый день. Но вот что держит на плаву:", "variables": [], "mood_categories": ["sadness", "calm"], "post_types": ["personal"]},
        {"template": "Без фильтров: {honest_thought}", "variables": ["honest_thought"], "mood_categories": ["calm"], "post_types": ["personal"]},

        # Реальность
        {"template": "Не буду врать — этот месяц был тяжёлым. Вот что помогло не сдаться:", "variables": [], "mood_categories": ["sadness"], "post_types": ["personal"]},
        {"template": "Устал от фраз 'просто работай больше'. Давай честно поговорим.", "variables": [], "mood_categories": ["sadness", "anger"], "post_types": ["personal"]},
        {"template": "Выгорание накрыло. Вот как справляюсь:", "variables": [], "mood_categories": ["sadness"], "post_types": ["personal"]},

        # Уязвимость
        {"template": "Сегодня особенно трудно.", "variables": [], "mood_categories": ["sadness"], "post_types": ["personal"]},
        {"template": "Признаюсь:", "variables": [], "mood_categories": ["calm"], "post_types": ["personal"]},
        {"template": "Никто не говорит об этой стороне бизнеса:", "variables": [], "mood_categories": ["calm"], "post_types": ["personal"]},
        {"template": "За кулисами:", "variables": [], "mood_categories": ["calm"], "post_types": ["personal"]},

        # Борьба
        {"template": "Сегодня держусь на кофеине и силе воли.", "variables": [], "mood_categories": ["sadness"], "post_types": ["personal"]},
        {"template": "Не сдаюсь, но устал.", "variables": [], "mood_categories": ["sadness"], "post_types": ["personal"]},
        {"template": "Пятый кофе за день:", "variables": [], "mood_categories": ["sadness"], "post_types": ["personal"]},

        # Raw моменты
        {"template": "Сижу в 3 ночи и думаю...", "variables": [], "mood_categories": ["calm", "sadness"], "post_types": ["personal"]},
        {"template": "Бессонница снова. Ну что ж.", "variables": [], "mood_categories": ["sadness"], "post_types": ["personal"]},
        {"template": "Иногда просто нужно выдохнуть.", "variables": [], "mood_categories": ["calm"], "post_types": ["personal"]},

        # Поддержка через уязвимость
        {"template": "Если тебе тоже тяжело — ты не один.", "variables": [], "mood_categories": ["sadness", "trust"], "post_types": ["personal"]},
        {"template": "Знаю, что не только у меня так.", "variables": [], "mood_categories": ["calm"], "post_types": ["personal"]},
        {"template": "Вот как я переживаю трудные дни:", "variables": [], "mood_categories": ["calm"], "post_types": ["personal"]},

        # Реалистичность
        {"template": "Не всегда всё радужно. Вот реальность:", "variables": [], "mood_categories": ["calm"], "post_types": ["personal"]},
        {"template": "Без прикрас:", "variables": [], "mood_categories": ["calm"], "post_types": ["personal"]},
        {"template": "Честный разговор о {topic}:", "variables": ["topic"], "mood_categories": ["calm"], "post_types": ["personal"]},
    ],
}


# ═══════════════════════════════════════════════════════════════════
# УТИЛИТЫ
# ═══════════════════════════════════════════════════════════════════

def get_total_hooks_count() -> int:
    """Подсчитывает общее количество hook'ов"""
    return sum(len(hooks) for hooks in HOOK_TEMPLATES.values())


# Автоматический подсчёт при импорте
TOTAL_HOOKS = get_total_hooks_count()

logger.info(f"[Hook Templates] Загружено {TOTAL_HOOKS} hook'ов для {len(HOOK_TEMPLATES)} версий персоны")
