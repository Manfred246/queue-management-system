"""Просмотр услуг и очередей из JSON-хранилища ПР3."""

from html import escape

from django.http import HttpRequest, HttpResponse

from homepage.views import page
from services import find_service_by_id
from storage import load_state


def services(request: HttpRequest) -> HttpResponse:
    """Показать список услуг со ссылками на карточки."""
    state = load_state()
    items = ""
    for service in state["services"].values():
        items += f"""
        <li class="list-group-item">
            <a href="/services/{service.id}/">{escape(service.name)}</a>
            — {service.average_service_time} мин.
        </li>
        """
    content = f"<h1>Услуги</h1><ul class='list-group'>{items}</ul>"
    return HttpResponse(page("Услуги", content))


def service_detail(request: HttpRequest, service_id: int) -> HttpResponse:
    """Найти услугу и показать её данные или вернуть 404."""
    state = load_state()
    service = find_service_by_id(state["services"], service_id)
    if service is None:
        content = """
        <h1 class="text-danger">Услуга не найдена</h1>
        <a class="btn btn-outline-secondary" href="/services/">К услугам</a>
        """
        return HttpResponse(page("Услуга не найдена", content), status=404)

    status = "доступна" if service.is_available else "недоступна"
    badge = "bg-success" if service.is_available else "bg-secondary"
    queues = ""
    for queue in state["queues"].values():
        if queue.service is service:
            queues += (
                f'<li><a href="/queues/{queue.id}/">'
                f'{escape(queue.name)}</a></li>'
            )
    content = f"""
    <h1>{escape(service.name)}</h1>
    <div class="card"><div class="card-body">
        <p>ID услуги: {service.id}</p>
        <p>Среднее время обслуживания: {service.average_service_time} мин.</p>
        <p>Услуга <span class="badge {badge}">{status}</span></p>
        <p>Очереди этой услуги:</p>
        <ul>{queues}</ul>
        <a class="btn btn-outline-secondary" href="/services/">К услугам</a>
    </div></div>
    """
    return HttpResponse(page(service.name, content))


def queues(request: HttpRequest) -> HttpResponse:
    """Показать очереди и связанные с ними услуги."""
    state = load_state()
    items = ""
    for queue in state["queues"].values():
        status = "открыта" if queue.is_open else "закрыта"
        items += f"""
        <li class="list-group-item">
            <a href="/queues/{queue.id}/">{escape(queue.name)}</a>
            — {escape(queue.service.name)}, {status}
        </li>
        """
    content = f"<h1>Очереди</h1><ul class='list-group'>{items}</ul>"
    return HttpResponse(page("Очереди", content))


def queue_detail(request: HttpRequest, queue_id: int) -> HttpResponse:
    """Показать состояние очереди и число активных талонов."""
    state = load_state()
    queue = state["queues"].get(queue_id)
    if queue is None:
        content = """
        <h1 class="text-danger">Очередь не найдена</h1>
        <a class="btn btn-outline-secondary" href="/queues/">К очередям</a>
        """
        return HttpResponse(page("Очередь не найдена", content), status=404)

    status = "открыта" if queue.is_open else "закрыта"
    issuing = "разрешена" if queue.can_issue_ticket() else "запрещена"
    active_count = len(queue.active_tickets(state["tickets"]))
    content = f"""
    <h1>{escape(queue.name)}</h1>
    <div class="card"><div class="card-body">
        <p>ID очереди: {queue.id}</p>
        <p>Услуга: <a href="/services/{queue.service.id}/">
            {escape(queue.service.name)}</a></p>
        <p>Очередь {status}. Выдача талонов {issuing}.</p>
        <p>Активных талонов: {active_count}</p>
        <a class="btn btn-outline-secondary" href="/queues/">К очередям</a>
    </div></div>
    """
    return HttpResponse(page(queue.name, content))
