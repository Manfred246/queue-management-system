"""Выдача, отмена и последовательное обслуживание талонов."""

from datetime import datetime

from queues import active_tickets
from utils import require_int


def can_issue_ticket(queue_is_open: bool, service_is_available: bool) -> bool:
    """Проверить возможность выдачи талона (функция из ПР1)."""
    return queue_is_open and service_is_available


def create_ticket_number(last_ticket_number: int) -> int:
    """Сформировать номер следующего талона (функция из ПР1)."""
    return require_int(last_ticket_number, 0) + 1


def calculate_wait_time(people_ahead: int, average_service_time: int) -> int:
    """Рассчитать приблизительное ожидание в минутах (ПР1)."""
    return (require_int(people_ahead, 0)
            * require_int(average_service_time))


def get_ticket_status(people_ahead: int) -> str:
    """Показать положение ожидающего талона (уточнённая функция ПР1)."""
    require_int(people_ahead, 0)
    if people_ahead == 0:
        return "Вы следующий"
    if people_ahead <= 3:
        return "Скоро ваша очередь"
    return "Ожидание в очереди"


def issue_ticket(
    tickets: list[dict], user: dict, service: dict, queue: dict,
) -> dict:
    """Связать посетителя, услугу и очередь новым талоном."""
    if user["role"] != "visitor":
        raise ValueError("Талон выдаётся только посетителю.")
    if queue["service_id"] != service["id"]:
        raise ValueError("Очередь не обслуживает выбранную услугу.")
    if not can_issue_ticket(queue["is_open"], service["is_available"]):
        raise ValueError("Очередь закрыта или услуга недоступна.")
    active = active_tickets(tickets, queue["id"])
    if any(item["user_id"] == user["id"] for item in active):
        raise ValueError("У посетителя уже есть активный талон в очереди.")
    number = create_ticket_number(queue["last_ticket_number"])
    ticket = {
        "id": max((item["id"] for item in tickets), default=0) + 1,
        "number": number, "user_id": user["id"],
        "service_id": service["id"], "queue_id": queue["id"],
        "status": "waiting", "issued_at": datetime.now().isoformat(),
    }
    tickets.append(ticket)
    queue["last_ticket_number"] = number
    return ticket


def find_ticket(tickets: list[dict], ticket_id: int) -> dict:
    """Найти талон по внутреннему идентификатору."""
    for ticket in tickets:
        if ticket["id"] == ticket_id:
            return ticket
    raise ValueError("Талон с таким ID не найден.")


def cancel_ticket(tickets: list[dict], ticket_id: int) -> None:
    """Отменить активный талон, сохранив его в истории."""
    ticket = find_ticket(tickets, ticket_id)
    if ticket["status"] not in ("waiting", "called"):
        raise ValueError("Талон уже завершён или отменён.")
    ticket["status"] = "cancelled"


def call_next_ticket(tickets: list[dict], queue_id: int) -> dict:
    """Вызвать первый ожидающий талон очереди по правилу FIFO."""
    active = active_tickets(tickets, queue_id)
    if any(item["status"] == "called" for item in active):
        raise ValueError("Сначала завершите текущий вызванный талон.")
    if not active:
        raise ValueError("Очередь пуста.")
    active[0]["status"] = "called"
    return active[0]


def complete_ticket(tickets: list[dict], ticket_id: int) -> None:
    """Завершить обслуживание ранее вызванного талона."""
    ticket = find_ticket(tickets, ticket_id)
    if ticket["status"] != "called":
        raise ValueError("Завершить можно только вызванный талон.")
    ticket["status"] = "completed"


def ticket_position(tickets: list[dict], ticket: dict) -> int:
    """Рассчитать число активных посетителей перед талоном."""
    return sum(item["number"] < ticket["number"] for item in
               active_tickets(tickets, ticket["queue_id"]))


def ticket_status(tickets: list[dict], ticket: dict) -> str:
    """Вернуть фактический статус с учётом порядка очереди."""
    if ticket["status"] == "waiting":
        return get_ticket_status(ticket_position(tickets, ticket))
    return {"called": "Вас вызывают к окну", "completed": "Обслужен",
            "cancelled": "Отменён"}[ticket["status"]]
