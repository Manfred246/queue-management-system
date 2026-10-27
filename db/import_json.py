"""Однократный перенос исходного JSON в пустые таблицы SQLite."""

import json
from pathlib import Path

from db.database import BASE_DIR, DB_PATH, get_connection
from validation import validate_data

JSON_PATH = BASE_DIR / "data" / "state.json"


def import_data(filename: Path = JSON_PATH, path: Path = DB_PATH) -> None:
    """Импортировать связанные записи одной транзакцией."""
    with Path(filename).open(encoding="utf-8") as stream:
        data = json.load(stream)
    validate_data(data)
    connection = get_connection(path)
    try:
        connection.executemany(
            "INSERT INTO users (id, name, role) VALUES (?, ?, ?)",
            [(item["id"], item["name"], item["role"])
             for item in data["users"]],
        )
        connection.executemany(
            """INSERT INTO services
               (id, name, average_service_time, is_available)
               VALUES (?, ?, ?, ?)""",
            [(item["id"], item["name"], item["average_service_time"],
              int(item["is_available"])) for item in data["services"]],
        )
        connection.executemany(
            """INSERT INTO queues
               (id, name, service_id, prefix, is_open, last_ticket_number)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [(item["id"], item["name"], item["service_id"], item["prefix"],
              int(item["is_open"]), item["last_ticket_number"])
             for item in data["queues"]],
        )
        connection.executemany(
            """INSERT INTO tickets
               (id, number, user_id, service_id, queue_id, status, issued_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            [(item["id"], item["number"], item["user_id"], item["service_id"],
              item["queue_id"], item["status"], item["issued_at"])
             for item in data["tickets"]],
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    import_data()
