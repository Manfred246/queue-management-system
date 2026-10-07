"""Функции работы с коллекцией услуг."""

from utils import next_id, require_bool, require_int, require_text


def add_service(services: dict, name: str, average_time: int) -> dict:
    """Добавить доступную услугу со средним временем обслуживания."""
    service = {
        "id": next_id(services), "name": require_text(name),
        "average_service_time": require_int(average_time),
        "is_available": True,
    }
    services[service["id"]] = service
    return service


def find_services(services: dict, query: str) -> list[dict]:
    """Найти услуги по подстроке названия без учёта регистра."""
    return [item for item in services.values()
            if query.casefold() in item["name"].casefold()]


def filter_services(services: dict, max_time: int) -> list[dict]:
    """Отобрать доступные услуги по длительности обслуживания."""
    require_int(max_time)
    return [item for item in services.values()
            if item["is_available"]
            and item["average_service_time"] <= max_time]


def sort_services(services: dict) -> list[dict]:
    """Упорядочить услуги по времени обслуживания и названию."""
    return sorted(services.values(), key=lambda item: (
        item["average_service_time"], item["name"].casefold()))


def set_service_available(service: dict, available: bool) -> None:
    """Изменить доступность отдельной услуги."""
    service["is_available"] = require_bool(available)
