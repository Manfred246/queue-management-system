from datetime import datetime


QUEUE_NAME = "Основная очередь"
QUEUE_IS_OPEN = True
LAST_TICKET_NUMBER = 24


def can_issue_ticket(queue_is_open, service_is_available):
    """Проверяет, можно ли выдать талон."""
    if queue_is_open and service_is_available:
        return True
    return False


def create_ticket_number(last_ticket_number):
    """Формирует номер следующего талона."""
    return last_ticket_number + 1


def calculate_wait_time(people_ahead, average_service_time):
    """Рассчитывает примерное время ожидания в минутах."""
    return people_ahead * average_service_time


def get_ticket_status(people_ahead):
    """Определяет текстовый статус талона."""
    if people_ahead == 0:
        return "Вас вызывают к окну"

    if people_ahead <= 3:
        return "Скоро ваша очередь"

    return "Ожидание в очереди"


print("=== Система управления очередью ===")

user_name = input("Введите имя посетителя: ").strip()

print("Доступные услуги:")
print("1 — Консультация")
print("2 — Оформление документов")

service_code = input("Выберите услугу (1 или 2): ").strip()

if service_code == "1":
    service_name = "Консультация"
    average_service_time = 7
    service_is_available = True

elif service_code == "2":
    service_name = "Оформление документов"
    average_service_time = 12
    service_is_available = True

else:
    service_name = "Неизвестная услуга"
    average_service_time = 0
    service_is_available = False


if service_is_available:
    people_ahead = int(
        input("Введите количество посетителей перед вами: ")
    )

    if people_ahead < 0:
        print("Количество посетителей не может быть отрицательным.")

    elif can_issue_ticket(QUEUE_IS_OPEN, service_is_available):
        ticket_number = create_ticket_number(LAST_TICKET_NUMBER)

        wait_time = calculate_wait_time(
            people_ahead,
            average_service_time,
        )

        ticket_status = get_ticket_status(people_ahead)

        issued_at = datetime.now()

        print()
        print("=== Талон выдан ===")
        print(f"Посетитель: {user_name}")
        print(f"Очередь: {QUEUE_NAME}")
        print(f"Услуга: {service_name}")
        print(f"Номер талона: A{ticket_number}")
        print(f"Людей перед вами: {people_ahead}")
        print(f"Ожидаемое время: {wait_time} мин.")
        print(f"Статус: {ticket_status}")

        print(
            "Время выдачи:",
            issued_at.strftime("%d.%m.%Y %H:%M"),
        )

    else:
        print("Сейчас талон получить нельзя: очередь закрыта.")

else:
    print("Указана неизвестная или недоступная услуга.")