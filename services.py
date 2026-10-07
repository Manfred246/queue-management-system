"""Услуга и функции обработки коллекции услуг."""

from utils import next_id, require_bool, require_int, require_text


class Service:
    """Вид обслуживания с длительностью и признаком доступности."""

    def __init__(
        self, service_id: int, name: str, average_service_time: int,
        is_available: bool = True,
    ) -> None:
        self.id = require_int(service_id)
        self.name = require_text(name)
        self.average_service_time = require_int(average_service_time)
        self._is_available = require_bool(is_available)

    @property
    def is_available(self) -> bool:
        """Текущая доступность услуги."""
        return self._is_available

    def set_available(self, available: bool) -> None:
        """Изменить доступность с проверкой значения."""
        self._is_available = require_bool(available)

    def __str__(self) -> str:
        available = "доступна" if self.is_available else "недоступна"
        return (
            f"{self.id}: {self.name}, "
            f"{self.average_service_time} мин., {available}"
        )


def add_service(
    services: dict[int, Service], name: str, average_time: int,
) -> Service:
    """Создать доступную услугу и добавить объект в коллекцию."""
    service = Service(next_id(services), name, average_time)
    services[service.id] = service
    return service


def find_services(services: dict[int, Service], query: str) -> list[Service]:
    """Найти услуги по подстроке названия без учёта регистра."""
    found = []
    for service in services.values():
        if query.casefold() in service.name.casefold():
            found.append(service)
    return found


def filter_services(
    services: dict[int, Service], max_time: int,
) -> list[Service]:
    """Отобрать доступные услуги по длительности обслуживания."""
    require_int(max_time)
    available = []
    for service in services.values():
        if service.is_available and service.average_service_time <= max_time:
            available.append(service)
    return available


def sort_services(services: dict[int, Service]) -> list[Service]:
    """Упорядочить услуги по времени обслуживания и названию."""
    return sorted(
        services.values(),
        key=lambda service: (
            service.average_service_time, service.name.casefold(),
        ),
    )
