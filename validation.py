"""Проверка структуры JSON и связности данных предметной области."""

from datetime import datetime

from utils import require_bool, require_int, require_text

COLLECTIONS = ("users", "services", "queues", "tickets")


def validate_data(data: dict) -> None:
    """Отклонить повреждённые данные до запуска меню или записи файла."""
    if not isinstance(data, dict) or set(data) != set(COLLECTIONS):
        raise ValueError("Неверный набор коллекций JSON.")
    indexed = {}
    for name in COLLECTIONS:
        if not isinstance(data[name], list):
            raise ValueError(f"Коллекция {name} должна быть списком.")
        indexed[name] = {}
        for item in data[name]:
            if not isinstance(item, dict):
                raise ValueError("Запись должна быть объектом JSON.")
            identifier = require_int(item["id"])
            if identifier in indexed[name]:
                raise ValueError("Повторяющийся идентификатор.")
            indexed[name][identifier] = item

    for user in data["users"]:
        require_text(user["name"])
        if user["role"] not in ("visitor", "employee"):
            raise ValueError("Неизвестная роль пользователя.")

    for service in data["services"]:
        require_text(service["name"])
        require_int(service["average_service_time"])
        require_bool(service["is_available"])

    prefixes = set()
    for queue in data["queues"]:
        require_text(queue["name"])
        prefix = require_text(queue["prefix"])
        if prefix in prefixes:
            raise ValueError("Префиксы очередей должны различаться.")
        prefixes.add(prefix)
        require_bool(queue["is_open"])
        require_int(queue["last_ticket_number"], 0)
        require_int(queue["service_id"])
        if queue["service_id"] not in indexed["services"]:
            raise ValueError("У очереди отсутствует услуга.")

    numbers = set()
    active_users = set()
    called_queues = set()
    for ticket in data["tickets"]:
        for field in ("user_id", "service_id", "queue_id", "number"):
            require_int(ticket[field])
        user = indexed["users"].get(ticket["user_id"])
        queue = indexed["queues"].get(ticket["queue_id"])
        if user is None or queue is None or user["role"] != "visitor":
            raise ValueError("Неверная связь талона с пользователем/очередью.")
        if ticket["service_id"] != queue["service_id"]:
            raise ValueError("Услуга талона не соответствует очереди.")
        if ticket["number"] > queue["last_ticket_number"]:
            raise ValueError("Счётчик очереди меньше номера талона.")
        key = (ticket["queue_id"], ticket["number"])
        if key in numbers:
            raise ValueError("Повторяющийся номер талона в очереди.")
        numbers.add(key)
        if ticket["status"] not in (
            "waiting", "called", "completed", "cancelled",
        ):
            raise ValueError("Неизвестный статус талона.")
        datetime.fromisoformat(require_text(ticket["issued_at"]))
        if ticket["status"] in ("waiting", "called"):
            key = (ticket["queue_id"], ticket["user_id"])
            if key in active_users:
                raise ValueError("Повторный активный талон посетителя.")
            active_users.add(key)
        if ticket["status"] == "called":
            if ticket["queue_id"] in called_queues:
                raise ValueError("В очереди вызвано несколько талонов.")
            called_queues.add(ticket["queue_id"])

    for ticket in data["tickets"]:
        if ticket["status"] != "called":
            continue
        for other in data["tickets"]:
            if other["queue_id"] != ticket["queue_id"]:
                continue
            if (other["status"] == "waiting"
                    and other["number"] < ticket["number"]):
                raise ValueError("Вызванный талон нарушает порядок очереди.")
