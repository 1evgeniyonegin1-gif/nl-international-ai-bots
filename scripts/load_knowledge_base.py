"""
Скрипт для загрузки документов в базу знаний RAG.
Поддерживает .txt, .md, .pdf файлы.
"""

import asyncio
import os
import re
import sys
from pathlib import Path
from typing import List, Optional

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.rag import VectorStore, EmbeddingService
from shared.rag.vector_store import get_vector_store
from shared.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentLoader:
    """Загрузчик документов в базу знаний."""

    # Максимальный размер чанка (в символах)
    CHUNK_SIZE = 1000
    # Перекрытие между чанками
    CHUNK_OVERLAP = 200

    def __init__(self, vector_store: VectorStore = None):
        self._vector_store = vector_store

    async def get_vector_store(self) -> VectorStore:
        if self._vector_store is None:
            self._vector_store = await get_vector_store()
        return self._vector_store

    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """
        Разбить текст на чанки с перекрытием.

        Args:
            text: Исходный текст
            chunk_size: Размер чанка
            overlap: Размер перекрытия

        Returns:
            Список чанков
        """
        chunk_size = chunk_size or self.CHUNK_SIZE
        overlap = overlap or self.CHUNK_OVERLAP

        # Чистим текст
        text = text.strip()
        if not text:
            return []

        # Разбиваем по параграфам или предложениям
        paragraphs = re.split(r'\n\n+', text)

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # Если параграф помещается в текущий чанк
            if len(current_chunk) + len(para) + 2 <= chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                # Сохраняем текущий чанк
                if current_chunk:
                    chunks.append(current_chunk)

                # Если параграф слишком большой, разбиваем по предложениям
                if len(para) > chunk_size:
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    current_chunk = ""
                    for sent in sentences:
                        if len(current_chunk) + len(sent) + 1 <= chunk_size:
                            if current_chunk:
                                current_chunk += " " + sent
                            else:
                                current_chunk = sent
                        else:
                            if current_chunk:
                                chunks.append(current_chunk)
                            current_chunk = sent
                else:
                    current_chunk = para

        # Добавляем последний чанк
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def read_text_file(self, file_path: Path) -> str:
        """Прочитать текстовый файл."""
        encodings = ['utf-8', 'cp1251', 'latin-1']
        for encoding in encodings:
            try:
                return file_path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Не удалось прочитать файл: {file_path}")

    def read_markdown(self, file_path: Path) -> str:
        """Прочитать Markdown файл (убираем разметку)."""
        text = self.read_text_file(file_path)
        # Убираем заголовки markdown
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
        # Убираем ссылки [text](url) -> text
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        # Убираем жирный/курсив
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)
        # Убираем код блоки
        text = re.sub(r'```[^`]*```', '', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        return text

    async def load_file(
        self,
        file_path: Path,
        category: str = None,
        metadata: dict = None
    ) -> int:
        """
        Загрузить один файл в базу знаний.

        Args:
            file_path: Путь к файлу
            category: Категория документа
            metadata: Дополнительные данные

        Returns:
            Количество добавленных чанков
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"Файл не найден: {file_path}")
            return 0

        # Определяем тип файла
        suffix = file_path.suffix.lower()

        if suffix in ['.txt', '.text']:
            text = self.read_text_file(file_path)
        elif suffix in ['.md', '.markdown']:
            text = self.read_markdown(file_path)
        else:
            logger.warning(f"Неподдерживаемый формат: {suffix}")
            return 0

        if not text.strip():
            logger.warning(f"Пустой файл: {file_path}")
            return 0

        # Разбиваем на чанки
        chunks = self.chunk_text(text)

        if not chunks:
            logger.warning(f"Нет чанков для файла: {file_path}")
            return 0

        # Готовим документы для загрузки
        documents = []
        for i, chunk in enumerate(chunks):
            doc = {
                "content": chunk,
                "source": file_path.name,
                "category": category,
                "chunk_index": i,
                "metadata": {
                    **(metadata or {}),
                    "file_path": str(file_path),
                    "total_chunks": len(chunks)
                }
            }
            documents.append(doc)

        # Загружаем в базу
        store = await self.get_vector_store()
        await store.add_documents(documents)

        logger.info(f"Загружено {len(chunks)} чанков из {file_path.name}")
        return len(chunks)

    async def load_directory(
        self,
        dir_path: Path,
        category: str = None,
        recursive: bool = True
    ) -> dict:
        """
        Загрузить все документы из директории.

        Args:
            dir_path: Путь к директории
            category: Категория по умолчанию
            recursive: Рекурсивный обход поддиректорий

        Returns:
            Статистика загрузки
        """
        dir_path = Path(dir_path)
        if not dir_path.is_dir():
            logger.error(f"Директория не найдена: {dir_path}")
            return {"error": "Directory not found"}

        stats = {
            "files_processed": 0,
            "chunks_added": 0,
            "errors": [],
            "files": []
        }

        # Находим все файлы
        patterns = ["*.txt", "*.md", "*.markdown"]
        files = []

        for pattern in patterns:
            if recursive:
                files.extend(dir_path.rglob(pattern))
            else:
                files.extend(dir_path.glob(pattern))

        logger.info(f"Найдено {len(files)} файлов в {dir_path}")

        for file_path in files:
            try:
                # Определяем категорию из имени поддиректории
                file_category = category
                if file_path.parent != dir_path:
                    file_category = file_path.parent.name

                chunks = await self.load_file(file_path, category=file_category)
                stats["files_processed"] += 1
                stats["chunks_added"] += chunks
                stats["files"].append({
                    "file": file_path.name,
                    "chunks": chunks,
                    "category": file_category
                })
            except Exception as e:
                logger.error(f"Ошибка при загрузке {file_path}: {e}")
                stats["errors"].append(str(file_path))

        return stats


async def main():
    """Главная функция для загрузки базы знаний."""
    print("=" * 60)
    print("📚 Загрузка документов в базу знаний RAG")
    print("=" * 60)

    # Путь к папке с документами
    project_root = Path(__file__).parent.parent
    knowledge_base_path = project_root / "content" / "knowledge_base"

    if not knowledge_base_path.exists():
        print(f"\n❌ Папка не найдена: {knowledge_base_path}")
        print("\n💡 Создайте папку и добавьте туда документы:")
        print(f"   {knowledge_base_path}")
        print("\nПоддерживаемые форматы: .txt, .md")
        return

    # Проверяем есть ли файлы
    files = list(knowledge_base_path.rglob("*.txt")) + list(knowledge_base_path.rglob("*.md"))

    if not files:
        print(f"\n⚠️  Папка {knowledge_base_path} пуста!")
        print("\n💡 Добавьте документы в папку:")
        print("   - Описание продуктов NL International")
        print("   - Маркетинг-план")
        print("   - Инструкции для партнёров")
        print("   - FAQ и частые вопросы")
        print("\nПоддерживаемые форматы: .txt, .md")
        return

    print(f"\n📁 Найдено {len(files)} файлов")
    print("\nЗагрузка...")

    # Инициализируем загрузчик
    loader = DocumentLoader()

    # Загружаем все документы
    stats = await loader.load_directory(knowledge_base_path)

    print("\n" + "=" * 60)
    print("📊 Результаты загрузки:")
    print("=" * 60)
    print(f"  Файлов обработано: {stats['files_processed']}")
    print(f"  Чанков добавлено:  {stats['chunks_added']}")

    if stats['errors']:
        print(f"\n⚠️  Ошибки ({len(stats['errors'])}):")
        for err in stats['errors']:
            print(f"   - {err}")

    if stats['files']:
        print("\n📄 Загруженные файлы:")
        for f in stats['files']:
            print(f"   - {f['file']}: {f['chunks']} чанков [{f['category'] or 'без категории'}]")

    # Показываем статистику базы
    store = await get_vector_store()
    db_stats = await store.get_stats()

    print("\n" + "=" * 60)
    print("📈 Статистика базы знаний:")
    print("=" * 60)
    print(f"  Всего документов: {db_stats['total_documents']}")
    print(f"  Размерность эмбеддингов: {db_stats['embedding_dimension']}")

    if db_stats['by_category']:
        print("\n  По категориям:")
        for cat, count in db_stats['by_category'].items():
            print(f"    - {cat}: {count}")

    print("\n✅ Загрузка завершена!")


if __name__ == "__main__":
    asyncio.run(main())
