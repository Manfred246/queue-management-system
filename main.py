"""Консольный интерфейс системы управления электронной очередью."""

from copy import deepcopy
from pathlib import Path

from queues import add_queue
from services import (
    Service, add_service, filter_services, find_services, sort_services,
)
from storage import DATA_FILE, load_state, save_state
from tickets import Ticket, find_ticket, issue_ticket
from users import add_user
from utils import input_int, input_text

MENU = """
1. Показать услуги (по времени обслуживания)
2. Найти услугу по названию
3. Отобрать доступные услуги по времени
4. Добавить услугу и очередь
5. Показать очереди
6. Открыть/закрыть очередь
7. Показать пользователей
8. Добавить пользователя
9. Получить талон
10. Показать талоны
11. Отменить талон
12. Вызвать следующего посетителя
13. Завершить обслуживание
14. Изменить доступность услуги
0. Выход
"""


def input_id(records: dict, prompt: str) -> int:
    """Прочитать ID и проверить, что запись существует."""
    identifier = input_int(prompt)
    if identifier not in records:
        raise ValueError("Запись с таким ID не найдена.")
    return identifier


def show_services(services: list[Service]) -> None:
    """Показать услуги, длительность и доступность."""
    for service in services:
        print(service)
    if not services:
        print("Услуги не найдены.")


def show_ticket(state: dict, ticket: Ticket) -> None:
    """Показать талон и текущую оценку ожидания, как в сценарии ПР1."""
    print(ticket)
    print(f"Очередь: {ticket.queue.name}")
    print("Статус:", ticket.status_text(state["tickets"]))
    if ticket.status == "waiting":
        ahead = ticket.position(state["tickets"])
        wait = ticket.wait_time(state["tickets"])
        print(f"Людей перед вами: {ahead}; ожидаемое время: {wait} мин.")
    print("Время выдачи:", ticket.issued_at.strftime("%d.%m.%Y %H:%M"))


def perform_action(state: dict, choice: str) -> bool:
    """Выполнить пункт меню; вернуть признак изменения данных."""
    services = state["services"]
    queues = state["queues"]
    users = state["users"]
    tickets = state["tickets"]

    if choice == "1":
        show_services(sort_services(services))
    elif choice == "2":
        query = input_text("Название: ")
        show_services(find_services(services, query))
    elif choice == "3":
        max_time = input_int("Максимум минут: ")
        show_services(filter_services(services, max_time))
    elif choice == "4":
        name = input_text("Название услуги: ")
        minutes = input_int("Среднее время обслуживания (мин.): ")
        prefix = input_text("Уникальный префикс талонов: ")
        service = add_service(services, name, minutes)
        add_queue(queues, service, f"Очередь: {name}", prefix)
    elif choice == "5":
        for queue in queues.values():
            print(queue)
    elif choice == "6":
        queue_id = input_id(queues, "ID очереди: ")
        queue = queues[queue_id]
        queue.set_open(not queue.is_open)
    elif choice == "7":
        for user in users.values():
            print(user)
        if not users:
            print("Пользователей пока нет. Добавьте пользователя (пункт 8).")
    elif choice == "8":
        name = input_text("Имя: ")
        role = input_text("Роль (visitor / employee): ")
        user = add_user(users, name, role)
        print(f"Пользователь добавлен, ID {user.id}.")
    elif choice == "9":
        user_id = input_id(users, "ID посетителя: ")
        service_id = input_id(services, "ID услуги: ")
        queue_id = input_id(queues, "ID очереди: ")
        ticket = issue_ticket(
            tickets, users[user_id], services[service_id], queues[queue_id],
        )
        print("=== Талон выдан ===")
        show_ticket(state, ticket)
    elif choice == "10":
        for ticket in tickets:
            show_ticket(state, ticket)
            print()
        if not tickets:
            print("Талонов пока нет.")
    elif choice == "11":
        ticket_id = input_int("ID талона: ")
        ticket = find_ticket(tickets, ticket_id)
        ticket.cancel()
    elif choice == "12":
        queue_id = input_id(queues, "ID очереди: ")
        ticket = queues[queue_id].call_next(tickets)
        show_ticket(state, ticket)
    elif choice == "13":
        ticket_id = input_int("ID талона: ")
        ticket = find_ticket(tickets, ticket_id)
        ticket.complete()
    elif choice == "14":
        service_id = input_id(services, "ID услуги: ")
        service = services[service_id]
        service.set_available(not service.is_available)
    else:
        raise ValueError("Неизвестный пункт меню.")
    return choice in {"4", "6", "8", "9", "11", "12", "13", "14"}


def main(filename: Path = DATA_FILE) -> None:
    """Загрузить состояние и обслуживать меню до выхода пользователя."""
    print("=== Система управления очередью ===")
    try:
        state = load_state(filename)
    except (OSError, ValueError) as error:
        print(f"Ошибка загрузки: {error}")
        return
    try:
        while True:
            print(MENU)
            choice = input("Выберите действие: ").strip()
            if choice == "0":
                break
            # Изменения применяются к копии: ошибка не портит рабочие данные.
            candidate = deepcopy(state)
            try:
                if perform_action(candidate, choice):
                    save_state(candidate, filename)
                    state = candidate
                    print("Изменения сохранены.")
            except (ValueError, OSError) as error:
                print(f"Операция не выполнена: {error}")
    except (EOFError, KeyboardInterrupt):
        print("\nРабота завершена.")


if __name__ == "__main__":
    main()
