"""Консольный интерфейс системы управления электронной очередью."""

from copy import deepcopy
from datetime import datetime
from pathlib import Path

from queues import add_queue, set_queue_open
from services import (
    add_service, filter_services, find_services, set_service_available,
    sort_services,
)
from storage import DATA_FILE, load_state, save_state
from tickets import (
    calculate_wait_time, call_next_ticket, cancel_ticket, complete_ticket,
    issue_ticket, ticket_position, ticket_status,
)
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


def select_record(records: dict, prompt: str) -> dict:
    """Выбрать существующую сущность по ID без аварийного завершения."""
    identifier = input_int(prompt)
    if identifier not in records:
        raise ValueError("Запись с таким ID не найдена.")
    return records[identifier]


def show_services(services: list[dict]) -> None:
    """Показать услуги, длительность и доступность."""
    for service in services:
        available = "доступна" if service["is_available"] else "недоступна"
        print(f'{service["id"]}: {service["name"]}, '
              f'{service["average_service_time"]} мин., {available}')
    if not services:
        print("Услуги не найдены.")


def show_ticket(state: dict, ticket: dict) -> None:
    """Показать талон и текущую оценку ожидания, как в сценарии ПР1."""
    queue = state["queues"][ticket["queue_id"]]
    service = state["services"][ticket["service_id"]]
    user = state["users"][ticket["user_id"]]
    print(f'ID {ticket["id"]}: {queue["prefix"]}{ticket["number"]}')
    print(f'Посетитель: {user["name"]}; услуга: {service["name"]}')
    print(f'Очередь: {queue["name"]}')
    print("Статус:", ticket_status(state["tickets"], ticket))
    if ticket["status"] == "waiting":
        ahead = ticket_position(state["tickets"], ticket)
        wait = calculate_wait_time(ahead, service["average_service_time"])
        print(f"Людей перед вами: {ahead}; ожидаемое время: {wait} мин.")
    issued_at = datetime.fromisoformat(ticket["issued_at"])
    print("Время выдачи:", issued_at.strftime("%d.%m.%Y %H:%M"))


def perform_action(state: dict, choice: str) -> bool:
    """Выполнить пункт меню; вернуть признак изменения данных."""
    services, queues = state["services"], state["queues"]
    users, tickets = state["users"], state["tickets"]
    if choice == "1":
        show_services(sort_services(services))
    elif choice == "2":
        show_services(find_services(services, input_text("Название: ")))
    elif choice == "3":
        show_services(filter_services(services, input_int("Максимум минут: ")))
    elif choice == "4":
        name = input_text("Название услуги: ")
        minutes = input_int("Среднее время обслуживания (мин.): ")
        prefix = input_text("Уникальный префикс талонов: ")
        service = add_service(services, name, minutes)
        add_queue(queues, service, f"Очередь: {name}", prefix)
    elif choice == "5":
        for queue in queues.values():
            status = "открыта" if queue["is_open"] else "закрыта"
            print(f'{queue["id"]}: {queue["name"]}, {status}, '
                  f'услуга ID {queue["service_id"]}')
    elif choice == "6":
        queue = select_record(queues, "ID очереди: ")
        set_queue_open(queue, not queue["is_open"])
    elif choice == "7":
        for user in users.values():
            role = "посетитель" if user["role"] == "visitor" else "сотрудник"
            print(f'{user["id"]}: {user["name"]}, {role}')
        if not users:
            print("Пользователей пока нет. Добавьте пользователя (пункт 8).")
    elif choice == "8":
        name = input_text("Имя: ")
        role = input_text("Роль (visitor / employee): ")
        user = add_user(users, name, role)
        print(f'Пользователь добавлен, ID {user["id"]}.')
    elif choice == "9":
        user = select_record(users, "ID посетителя: ")
        service = select_record(services, "ID услуги: ")
        queue = select_record(queues, "ID очереди: ")
        ticket = issue_ticket(tickets, user, service, queue)
        print("=== Талон выдан ===")
        show_ticket(state, ticket)
    elif choice == "10":
        for ticket in tickets:
            show_ticket(state, ticket)
            print()
        if not tickets:
            print("Талонов пока нет.")
    elif choice == "11":
        cancel_ticket(tickets, input_int("ID талона: "))
    elif choice == "12":
        queue = select_record(queues, "ID очереди: ")
        show_ticket(state, call_next_ticket(tickets, queue["id"]))
    elif choice == "13":
        complete_ticket(tickets, input_int("ID талона: "))
    elif choice == "14":
        service = select_record(services, "ID услуги: ")
        set_service_available(service, not service["is_available"])
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
