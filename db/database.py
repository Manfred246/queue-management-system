"""Подключение к отдельной базе предметной области ПР7."""

import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "queue.sqlite"
SCHEMA_PATH = BASE_DIR / "sql" / "schema.sql"


def get_connection(path: Path = DB_PATH) -> sqlite3.Connection:
    """Открыть базу с проверкой связей и доступом к полям по именам."""
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_tables(path: Path = DB_PATH) -> None:
    """Создать таблицы; существующие таблицы и данные сохраняются."""
    connection = get_connection(path)
    try:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    create_tables()
