"""Просмотр талонов и их связей с объектами ПР3."""

from html import escape

from django.http import HttpRequest, HttpResponse

from homepage.views import page
from storage import load_state
from tickets import find_ticket


def tickets(request: HttpRequest) -> HttpResponse:
    """Показать сохранённые талоны и их текущие статусы."""
    state = load_state()
    items = ""
    for ticket in state["tickets"]:
        status = ticket.status_text(state["tickets"])
        items += f"""
        <li class="list-group-item">
            <a href="/tickets/{ticket.id}/">{escape(ticket.display_number)}</a>
            — {escape(ticket.user.name)}, {escape(ticket.service.name)}
            <span class="badge bg-secondary">{status}</span>
        </li>
        """
    if not items:
        items = '<li class="list-group-item">Талонов пока нет.</li>'
    content = f"<h1>Талоны</h1><ul class='list-group'>{items}</ul>"
    return HttpResponse(page("Талоны", content))


def ticket_detail(request: HttpRequest, ticket_id: int) -> HttpResponse:
    """Показать талон с данными посетителя, услуги и очереди."""
    state = load_state()
    try:
        ticket = find_ticket(state["tickets"], ticket_id)
    except ValueError:
        content = """
        <h1 class="text-danger">Талон не найден</h1>
        <a class="btn btn-outline-secondary" href="/tickets/">К талонам</a>
        """
        return HttpResponse(page("Талон не найден", content), status=404)

    status = ticket.status_text(state["tickets"])
    issued_at = ticket.issued_at.strftime("%d.%m.%Y %H:%M")
    wait = ticket.wait_time(state["tickets"])
    content = f"""
    <h1>Талон {escape(ticket.display_number)}</h1>
    <div class="card"><div class="card-body">
        <p>ID талона: {ticket.id}</p>
        <p>Посетитель: {escape(ticket.user.name)}</p>
        <p>Услуга: <a href="/services/{ticket.service.id}/">
            {escape(ticket.service.name)}</a></p>
        <p>Очередь: <a href="/queues/{ticket.queue.id}/">
            {escape(ticket.queue.name)}</a></p>
        <p>Статус: <span class="badge bg-secondary">{status}</span></p>
        <p>Время выдачи: {issued_at}</p>
        <p>Ожидание: {wait} мин.</p>
        <a class="btn btn-outline-secondary" href="/tickets/">К талонам</a>
    </div></div>
    """
    return HttpResponse(page(f"Талон {ticket.display_number}", content))
