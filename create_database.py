"""
Скрипт для создания базы данных PostgreSQL
"""
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Параметры подключения
DB_HOST = "localhost"
DB_PORT = "5432"
DB_USER = "postgres"
DB_PASSWORD = "UB8TG6@@IUYDGC"
DB_NAME = "nl_international"

def create_database():
    """Создает базу данных если её нет"""

    print(f"🔄 Подключаемся к PostgreSQL...")

    try:
        # Подключаемся к служебной базе postgres
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres"
        )

        # Устанавливаем автокоммит для создания БД
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        # Проверяем существует ли база
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DB_NAME,)
        )
        exists = cursor.fetchone()

        if exists:
            print(f"✅ База данных '{DB_NAME}' уже существует!")
        else:
            # Создаем базу данных
            cursor.execute(
                sql.SQL("CREATE DATABASE {}").format(
                    sql.Identifier(DB_NAME)
                )
            )
            print(f"✅ База данных '{DB_NAME}' успешно создана!")

        cursor.close()
        conn.close()

        print(f"\n🎉 Готово! База данных настроена.")
        print(f"📍 Подключение: postgresql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}")

        return True

    except psycopg2.OperationalError as e:
        print(f"\n❌ Ошибка подключения к PostgreSQL:")
        print(f"   {e}")
        print(f"\n💡 Проверьте:")
        print(f"   1. PostgreSQL запущен")
        print(f"   2. Пароль правильный: {DB_PASSWORD}")
        print(f"   3. Порт доступен: {DB_PORT}")
        return False

    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Создание базы данных для NL International AI Bot")
    print("=" * 60)
    print()

    success = create_database()

    if success:
        print("\n✨ Можно переходить к следующему шагу!")
    else:
        print("\n⚠️  Исправьте ошибки и запустите скрипт снова")

    input("\nНажмите Enter для выхода...")
