"""Функции работы с очередями и их порядком обслуживания."""

from utils import next_id, require_bool, require_int, require_text


def add_queue(
    queues: dict, service: dict, name: str, prefix: str,
    last_ticket_number: int = 0,
) -> dict:
    """Создать отдельную очередь для выбранной услуги."""
    prefix = require_text(prefix)
    if any(item["prefix"] == prefix for item in queues.values()):
        raise ValueError("Префикс талонов уже используется.")
    queue = {
        "id": next_id(queues), "service_id": service["id"],
        "name": require_text(name), "prefix": prefix, "is_open": True,
        "last_ticket_number": require_int(last_ticket_number, 0),
    }
    queues[queue["id"]] = queue
    return queue


def set_queue_open(queue: dict, is_open: bool) -> None:
    """Открыть или закрыть выдачу новых талонов."""
    queue["is_open"] = require_bool(is_open)


def active_tickets(tickets: list[dict], queue_id: int) -> list[dict]:
    """Вернуть активные талоны очереди в порядке выдачи."""
    return sorted(
        (item for item in tickets if item["queue_id"] == queue_id
         and item["status"] in ("waiting", "called")),
        key=lambda item: item["number"],
    )
