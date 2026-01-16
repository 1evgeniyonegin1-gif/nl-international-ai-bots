# RAG система - Статус

## ТЕКУЩИЙ СТАТУС: ГОТОВО К РАБОТЕ

**Дата проверки:** 16 января 2026

---

## Что сделано:

### Код RAG системы
- [x] Скрипт загрузки документов (`scripts/load_knowledge_base.py`)
- [x] Сервис эмбеддингов (`shared/rag/embeddings.py`) - бесплатная локальная модель
- [x] Векторное хранилище (`shared/rag/vector_store.py`) - PostgreSQL + pgvector
- [x] RAG движок для поиска (`shared/rag/rag_engine.py`)
- [x] Промпты для использования базы знаний

### База данных
- [x] PostgreSQL установлен и работает
- [x] Расширение pgvector установлено
- [x] Таблица `knowledge_documents` создана

### База знаний загружена
- [x] **200 документов** (чанков) в базе
- [x] Категории: products, business, faq, training, company

---

## Статистика базы знаний:

| Категория | Описание |
|-----------|----------|
| **products** | Продукты NL: Energy Diet, БАДы, коллаген, косметика |
| **business** | Маркетинг-план, вознаграждения, реферальная система |
| **faq** | Оформление заказа, скидки, партнерство |
| **training** | Работа с возражениями, советы новичкам, соцсети |
| **company** | Информация о компании NL International |

---

## Файлы базы знаний:

```
content/knowledge_base/
├── products/
│   ├── energy_diet.md
│   ├── bady_i_adaptogeny.md
│   ├── collagen.md
│   ├── collagen_full.md
│   ├── slim_pohudeniye.md
│   └── kosmetika_nl.md
├── business/
│   ├── plan_voznagrazhdeniya.md
│   └── referalnye_ssylki.md
├── company/
│   └── about_nl.md
├── faq/
│   ├── oformlenie_zakaza.md
│   └── skidka_i_partnerstvo.md
└── training/
    ├── rabota_s_vozrazheniyami.md
    ├── sovety_novichkam.md
    └── vedenie_socsetey.md
```

---

## Как перезагрузить базу знаний:

Если нужно обновить документы после редактирования:

```bash
cd "c:\Users\mafio\OneDrive\Документы\projects\nl-international-ai-bots"
python scripts/load_knowledge_base.py --clear
```

Флаг `--clear` удалит старые документы перед загрузкой новых.

---

## Как добавить новые документы:

1. Создай `.md` или `.txt` файл в соответствующей папке `content/knowledge_base/`
2. Запусти `python scripts/load_knowledge_base.py --clear`
3. Бот автоматически начнёт использовать новые данные

---

## Проверка работы RAG:

```bash
python -c "
import psycopg2
conn = psycopg2.connect(host='localhost', port='5432', user='postgres', password='UB8TG6@@IUYDGC', database='nl_international')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM knowledge_documents')
print('Documents:', cur.fetchone()[0])
cur.execute('SELECT DISTINCT category FROM knowledge_documents')
print('Categories:', [c[0] for c in cur.fetchall()])
conn.close()
"
```

---

## ГОТОВО!

RAG система полностью настроена и готова к использованию AI-Куратором.
