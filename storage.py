"""Загрузка и сохранение пользователей, услуг, очередей и талонов."""

import json
from datetime import datetime
from pathlib import Path

from queues import Queue
from services import Service
from tickets import Ticket
from users import User
from validation import validate_data

DATA_FILE = Path(__file__).resolve().parent / "data" / "state.json"


def default_state() -> dict:
    """Создать стартовые данные, продолжая настройки ПР1."""
    consultation = Service(1, "Консультация", 7)
    documents = Service(2, "Оформление документов", 12)
    return {
        "users": {},
        "tickets": [],
        "services": {1: consultation, 2: documents},
        "queues": {
            1: Queue(
                1, consultation, "Основная очередь", "A",
                last_ticket_number=24,
            ),
            2: Queue(2, documents, "Очередь документов", "B"),
        },
    }


def state_to_data(state: dict) -> dict:
    """Преобразовать объекты в JSON-записи, заменив ссылки на ID."""
    return {
        "users": [
            {"id": user.id, "name": user.name, "role": user.role}
            for user in state["users"].values()
        ],
        "services": [
            {
                "id": service.id,
                "name": service.name,
                "average_service_time": service.average_service_time,
                "is_available": service.is_available,
            }
            for service in state["services"].values()
        ],
        "queues": [
            {
                "id": queue.id,
                "name": queue.name,
                "service_id": queue.service.id,
                "prefix": queue.prefix,
                "is_open": queue.is_open,
                "last_ticket_number": queue.last_ticket_number,
            }
            for queue in state["queues"].values()
        ],
        "tickets": [
            {
                "id": ticket.id,
                "number": ticket.number,
                "user_id": ticket.user.id,
                "service_id": ticket.service.id,
                "queue_id": ticket.queue.id,
                "status": ticket.status,
                "issued_at": ticket.issued_at.isoformat(),
            }
            for ticket in state["tickets"]
        ],
    }


def data_to_state(data: dict) -> dict:
    """Создать объекты и восстановить ссылки на общие экземпляры."""
    validate_data(data)
    users = {}
    for item in data["users"]:
        user = User(item["id"], item["name"], item["role"])
        users[user.id] = user

    services = {}
    for item in data["services"]:
        service = Service(
            item["id"], item["name"], item["average_service_time"],
            is_available=item["is_available"],
        )
        services[service.id] = service

    # Сначала создаются услуги, затем связанные с ними очереди.
    queues = {}
    for item in data["queues"]:
        service = services[item["service_id"]]
        queue = Queue(
            item["id"], service, item["name"], item["prefix"],
            is_open=item["is_open"],
            last_ticket_number=item["last_ticket_number"],
        )
        queues[queue.id] = queue

    tickets = []
    for item in data["tickets"]:
        ticket = Ticket(
            item["id"], item["number"],
            users[item["user_id"]], services[item["service_id"]],
            queues[item["queue_id"]],
            issued_at=datetime.fromisoformat(item["issued_at"]),
            status=item["status"],
        )
        tickets.append(ticket)

    return {
        "users": users,
        "services": services,
        "queues": queues,
        "tickets": tickets,
    }


def load_state(filename: Path = DATA_FILE) -> dict:
    """Прочитать данные; при отсутствии файла создать начальное состояние."""
    try:
        with Path(filename).open(encoding="utf-8") as stream:
            data = json.load(stream)
    except FileNotFoundError:
        return default_state()
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError(f"Не удалось прочитать JSON: {error}") from error
    try:
        return data_to_state(data)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Некорректные данные JSON: {error}") from error


def save_state(state: dict, filename: Path = DATA_FILE) -> None:
    """Заменить файл целиком только после успешной записи всех данных."""
    data = state_to_data(state)
    validate_data(data)
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        # Основной файл заменяется только после успешной записи.
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
