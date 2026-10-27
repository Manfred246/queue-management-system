"""Данные услуг и очередей для Django-шаблонов."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from services import find_service_by_id
from storage import load_state


def services(request: HttpRequest) -> HttpResponse:
    """Передать список услуг в шаблон."""
    state = load_state()
    context = {"services": list(state["services"].values())}
    return render(request, "catalog/service_list.html", context)


def service_detail(request: HttpRequest, service_id: int) -> HttpResponse:
    """Передать услугу и её очереди в шаблон карточки."""
    state = load_state()
    service = find_service_by_id(state["services"], service_id)
    service_queues = []
    if service is not None:
        for queue in state["queues"].values():
            if queue.service is service:
                service_queues.append(queue)
    context = {"service": service, "queues": service_queues}
    return render(
        request, "catalog/service_detail.html", context,
        status=404 if service is None else 200,
    )


def queues(request: HttpRequest) -> HttpResponse:
    """Передать список очередей в шаблон."""
    state = load_state()
    context = {"queues": list(state["queues"].values())}
    return render(request, "catalog/queue_list.html", context)


def queue_detail(request: HttpRequest, queue_id: int) -> HttpResponse:
    """Передать очередь и число активных талонов в шаблон."""
    state = load_state()
    queue = state["queues"].get(queue_id)
    active_count = 0
    if queue is not None:
        active_count = len(queue.active_tickets(state["tickets"]))
    context = {"queue": queue, "active_count": active_count}
    return render(
        request, "catalog/queue_detail.html", context,
        status=404 if queue is None else 200,
    )
