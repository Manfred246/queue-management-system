"""Талон и функции обработки коллекции талонов."""

from __future__ import annotations

from datetime import datetime

from queues import Queue
from services import Service
from users import User
from utils import require_int


def calculate_wait_time(people_ahead: int, average_service_time: int) -> int:
    """Рассчитать приблизительное ожидание в минутах (ПР1)."""
    require_int(people_ahead, 0)
    require_int(average_service_time)
    return people_ahead * average_service_time


def get_ticket_status(people_ahead: int) -> str:
    """Показать положение ожидающего талона (уточнённая функция ПР1)."""
    require_int(people_ahead, 0)
    if people_ahead == 0:
        return "Вы следующий"
    if people_ahead <= 3:
        return "Скоро ваша очередь"
    return "Ожидание в очереди"


class Ticket:
    """Талон, связывающий объекты посетителя, услуги и очереди."""

    STATUSES = ("waiting", "called", "completed", "cancelled")

    def __init__(
        self, ticket_id: int, number: int, user: User, service: Service,
        queue: Queue, issued_at: datetime | None = None,
        status: str = "waiting",
    ) -> None:
        if not isinstance(user, User) or not user.can_receive_ticket():
            raise ValueError("Талон выдаётся только посетителю.")
        if not isinstance(queue, Queue) or queue.service is not service:
            raise ValueError("Очередь не обслуживает выбранную услугу.")
        if status not in self.STATUSES:
            raise ValueError("Неизвестный статус талона.")
        if issued_at is not None and not isinstance(issued_at, datetime):
            raise ValueError("Время выдачи должно быть datetime.")
        self.id = require_int(ticket_id)
        self.number = require_int(number)
        self.user = user
        self.service = service
        self.queue = queue
        if issued_at is None:
            issued_at = datetime.now()
        self.issued_at = issued_at
        # При восстановлении JSON допустим любой сохранённый статус.
        self._status = status

    @property
    def status(self) -> str:
        """Статус доступен для чтения; переходы выполняются методами."""
        return self._status

    @property
    def is_active(self) -> bool:
        """Участвует ли талон в ожидании или обслуживании."""
        return self.status in ("waiting", "called")

    @property
    def display_number(self) -> str:
        """Номер талона с префиксом очереди."""
        return f"{self.queue.prefix}{self.number}"

    def cancel(self) -> None:
        """Отменить активный талон без удаления из истории."""
        if not self.is_active:
            raise ValueError("Талон уже завершён или отменён.")
        self._status = "cancelled"

    def call(self, tickets: list[Ticket]) -> None:
        """Вызвать ожидающий талон с соблюдением порядка очереди."""
        active = self.queue.active_tickets(tickets)
        for ticket in active:
            if ticket.status == "called":
                raise ValueError("Сначала завершите текущий вызванный талон.")
        if self.status != "waiting" or not active or active[0] is not self:
            raise ValueError("Вызвать можно только первый ожидающий талон.")
        self._status = "called"

    def complete(self) -> None:
        """Завершить обслуживание вызванного талона."""
        if self.status != "called":
            raise ValueError("Завершить можно только вызванный талон.")
        self._status = "completed"

    def position(self, tickets: list[Ticket]) -> int:
        """Определить число активных посетителей перед талоном."""
        people_ahead = 0
        for ticket in self.queue.active_tickets(tickets):
            if ticket.number < self.number:
                people_ahead += 1
        return people_ahead

    def wait_time(self, tickets: list[Ticket]) -> int:
        """Рассчитать ожидание только для ожидающего талона."""
        if self.status != "waiting":
            return 0
        return calculate_wait_time(
            self.position(tickets), self.service.average_service_time,
        )

    def status_text(self, tickets: list[Ticket]) -> str:
        """Получить статус для вывода посетителю."""
        if self.status == "waiting":
            return get_ticket_status(self.position(tickets))
        if self.status == "called":
            return "Вас вызывают к окну"
        if self.status == "completed":
            return "Обслужен"
        return "Отменён"

    def __str__(self) -> str:
        return (
            f"ID {self.id}: {self.display_number}, {self.user.name}, "
            f"{self.service.name}, {self.status}"
        )


def issue_ticket(
    tickets: list[Ticket], user: User, service: Service, queue: Queue,
) -> Ticket:
    """Проверить коллекцию и добавить новый объект талона."""
    if not queue.can_issue_ticket():
        raise ValueError("Очередь закрыта или услуга недоступна.")
    for ticket in queue.active_tickets(tickets):
        if ticket.user.id == user.id:
            raise ValueError("У посетителя уже есть активный талон в очереди.")
    ticket_id = max([ticket.id for ticket in tickets], default=0) + 1
    ticket = Ticket(
        ticket_id, queue.next_ticket_number(), user, service, queue,
    )
    queue.record_ticket_number(ticket.number)
    tickets.append(ticket)
    return ticket


def find_ticket(tickets: list[Ticket], ticket_id: int) -> Ticket:
    """Найти объект талона по внутреннему идентификатору."""
    for ticket in tickets:
        if ticket.id == ticket_id:
            return ticket
    raise ValueError("Талон с таким ID не найден.")
