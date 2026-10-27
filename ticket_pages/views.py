"""Данные талонов и связанных объектов для Django-шаблонов."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from storage import load_state
from tickets import find_ticket


def tickets(request: HttpRequest) -> HttpResponse:
    """Передать список талонов в шаблон."""
    state = load_state()
    context = {"tickets": state["tickets"]}
    return render(request, "ticket_pages/ticket_list.html", context)


def ticket_detail(request: HttpRequest, ticket_id: int) -> HttpResponse:
    """Найти талон, подготовить ожидание и передать данные в шаблон."""
    state = load_state()
    try:
        ticket = find_ticket(state["tickets"], ticket_id)
    except ValueError:
        ticket = None
    wait = 0
    if ticket is not None:
        wait = ticket.wait_time(state["tickets"])
    context = {"ticket": ticket, "wait": wait}
    return render(
        request, "ticket_pages/ticket_detail.html", context,
        status=404 if ticket is None else 200,
    )
