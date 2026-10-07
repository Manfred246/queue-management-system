"""Очередь, её поведение и функции обработки коллекций."""

from __future__ import annotations

from typing import TYPE_CHECKING

from services import Service
from utils import next_id, require_bool, require_int, require_text

if TYPE_CHECKING:
    # Импорт нужен только для аннотаций, чтобы избежать циклического импорта.
    from tickets import Ticket


def can_issue_ticket(queue_is_open: bool, service_is_available: bool) -> bool:
    """Проверить возможность выдачи талона (функция из ПР1)."""
    return queue_is_open and service_is_available


def create_ticket_number(last_ticket_number: int) -> int:
    """Сформировать номер следующего талона (функция из ПР1)."""
    return require_int(last_ticket_number, 0) + 1


class Queue:
    """Последовательность обслуживания талонов одной услуги."""

    def __init__(
        self, queue_id: int, service: Service, name: str, prefix: str,
        is_open: bool = True, last_ticket_number: int = 0,
    ) -> None:
        if not isinstance(service, Service):
            raise ValueError("Очередь должна быть связана с услугой.")
        self.id = require_int(queue_id)
        self.service = service
        self.name = require_text(name)
        self.prefix = require_text(prefix)
        self._is_open = require_bool(is_open)
        self._last_ticket_number = require_int(last_ticket_number, 0)

    @property
    def is_open(self) -> bool:
        """Разрешена ли выдача новых талонов."""
        return self._is_open

    @property
    def last_ticket_number(self) -> int:
        """Последний выданный номер; изменяется при выдаче талона."""
        return self._last_ticket_number

    def set_open(self, is_open: bool) -> None:
        """Открыть или закрыть выдачу новых талонов."""
        self._is_open = require_bool(is_open)

    def can_issue_ticket(self) -> bool:
        """Проверить состояние очереди и связанной услуги."""
        return can_issue_ticket(self.is_open, self.service.is_available)

    def next_ticket_number(self) -> int:
        """Получить очередной номер без изменения счётчика."""
        return create_ticket_number(self.last_ticket_number)

    def record_ticket_number(self, number: int) -> None:
        """Зафиксировать выданный последовательный номер."""
        if require_int(number) != self.next_ticket_number():
            raise ValueError("Номер талона должен следовать за последним.")
        self._last_ticket_number = number

    def active_tickets(self, tickets: list[Ticket]) -> list[Ticket]:
        """Получить активные талоны объекта очереди в порядке FIFO."""
        active = []
        for ticket in tickets:
            if ticket.queue.id == self.id and ticket.is_active:
                active.append(ticket)
        return sorted(active, key=lambda ticket: ticket.number)

    def call_next(self, tickets: list[Ticket]) -> Ticket:
        """Вызвать первого ожидающего посетителя этой очереди."""
        active = self.active_tickets(tickets)
        if not active:
            raise ValueError("Очередь пуста.")
        ticket = active[0]
        ticket.call(tickets)
        return ticket

    def __str__(self) -> str:
        status = "открыта" if self.is_open else "закрыта"
        return (
            f"{self.id}: {self.name}, {status}, "
            f"услуга ID {self.service.id}"
        )


def add_queue(
    queues: dict[int, Queue], service: Service, name: str, prefix: str,
    last_ticket_number: int = 0,
) -> Queue:
    """Создать очередь с уникальным префиксом и добавить её в коллекцию."""
    prefix = require_text(prefix)
    for queue in queues.values():
        if queue.prefix == prefix:
            raise ValueError("Префикс талонов уже используется.")
    queue = Queue(
        next_id(queues), service, name, prefix,
        last_ticket_number=last_ticket_number,
    )
    queues[queue.id] = queue
    return queue
