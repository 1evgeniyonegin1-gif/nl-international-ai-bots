"""
Установка расширения pgvector в PostgreSQL
"""
import psycopg2

# Параметры подключения
DB_HOST = "localhost"
DB_PORT = "5432"
DB_USER = "postgres"
DB_PASSWORD = "UB8TG6@@IUYDGC"
DB_NAME = "nl_international"

def install_pgvector():
    """Устанавливает расширение pgvector"""

    print("🔄 Подключаемся к базе данных...")

    try:
        # Подключаемся к базе
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        cursor = conn.cursor()

        # Устанавливаем расширение pgvector
        print("📦 Устанавливаем расширение pgvector...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()

        print("✅ Расширение pgvector успешно установлено!")

        # Проверяем что расширение установлено
        cursor.execute("SELECT extname FROM pg_extension WHERE extname = 'vector';")
        result = cursor.fetchone()

        if result:
            print(f"✅ Расширение подтверждено: {result[0]}")

        cursor.close()
        conn.close()

        print("\n🎉 Готово! Теперь можно запускать бота.")
        return True

    except psycopg2.OperationalError as e:
        print(f"\n❌ Ошибка подключения к PostgreSQL:")
        print(f"   {e}")
        return False

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Установка расширения pgvector для PostgreSQL")
    print("=" * 60)
    print()

    success = install_pgvector()

    if not success:
        print("\n⚠️  Исправьте ошибки и запустите скрипт снова")

    input("\nНажмите Enter для выхода...")
