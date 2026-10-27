"""Списки талонов, карточки и статистика на основе SQL-запросов."""

from datetime import datetime

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.database import get_connection


def prepare_ticket(row) -> dict:
    """Подготовить дату SQLite для фильтра date в шаблоне."""
    ticket = dict(row)
    ticket["issued_at"] = datetime.fromisoformat(ticket["issued_at"])
    return ticket


def tickets(request: HttpRequest) -> HttpResponse:
    """Показать активные талоны или всю историю по выбору посетителя."""
    state = request.GET.get("state", "active")
    if state not in ("active", "all", "cancelled"):
        state = "active"
    connection = get_connection()
    try:
        rows = connection.execute("""
            SELECT t.id, t.status, t.issued_at,
                   q.prefix || t.number AS display_number,
                   u.name AS user_name, s.name AS service_name
            FROM tickets AS t
            JOIN queues AS q ON t.queue_id = q.id
            JOIN users AS u ON t.user_id = u.id
            JOIN services AS s ON t.service_id = s.id
            WHERE ? = 'all'
               OR (? = 'active' AND t.status IN ('waiting', 'called'))
               OR (? = 'cancelled' AND t.status = 'cancelled')
            ORDER BY t.issued_at, t.id
        """, (state, state, state)).fetchall()
    finally:
        connection.close()
    context = {
        "tickets": [prepare_ticket(row) for row in rows], "state": state,
    }
    return render(request, "ticket_pages/ticket_list.html", context)


def ticket_detail(request: HttpRequest, ticket_id: int) -> HttpResponse:
    """Получить связанные данные талона и оценку ожидания."""
    connection = get_connection()
    wait = 0
    try:
        row = connection.execute("""
            SELECT t.id, t.number, t.queue_id, t.service_id, t.status,
                   t.issued_at, q.prefix || t.number AS display_number,
                   q.name AS queue_name, s.name AS service_name,
                   s.average_service_time, u.name AS user_name
            FROM tickets AS t
            JOIN queues AS q ON t.queue_id = q.id
            JOIN services AS s ON t.service_id = s.id
            JOIN users AS u ON t.user_id = u.id
            WHERE t.id = ?
        """, (ticket_id,)).fetchone()
        ticket = prepare_ticket(row) if row is not None else None
        if ticket is not None and ticket["status"] == "waiting":
            result = connection.execute("""
                SELECT COUNT(*) AS people_ahead FROM tickets
                WHERE queue_id = ? AND number < ?
                  AND status IN ('waiting', 'called')
            """, (ticket["queue_id"], ticket["number"])).fetchone()
            wait = result["people_ahead"] * ticket["average_service_time"]
    finally:
        connection.close()
    return render(
        request, "ticket_pages/ticket_detail.html",
        {"ticket": ticket, "wait": wait},
        status=404 if ticket is None else 200,
    )


def statistics(request: HttpRequest) -> HttpResponse:
    """Показать нагрузку очередей и услуг, включая нулевые группы."""
    min_count = request.GET.get("min_count", "0")
    error = ""
    try:
        threshold = int(min_count)
        if threshold < 0:
            raise ValueError
    except ValueError:
        threshold = 0
        min_count = "0"
        error = "Порог должен быть неотрицательным целым числом."
    connection = get_connection()
    try:
        active = connection.execute("""
            SELECT COUNT(*) AS active_count FROM tickets
            WHERE status IN ('waiting', 'called')
        """).fetchone()
        average = connection.execute("""
            SELECT AVG(average_service_time) AS average_minutes
            FROM services WHERE is_available = 1
        """).fetchone()
        queue_statistics = connection.execute("""
            SELECT q.id, q.name, COUNT(t.id) AS ticket_count
            FROM queues AS q
            LEFT JOIN tickets AS t ON t.queue_id = q.id
                AND t.status IN ('waiting', 'called')
            GROUP BY q.id, q.name
            HAVING COUNT(t.id) >= ?
            ORDER BY ticket_count DESC, q.id
        """, (threshold,)).fetchall()
        service_statistics = connection.execute("""
            SELECT s.id, s.name, COUNT(t.id) AS ticket_count
            FROM services AS s
            LEFT JOIN tickets AS t ON t.service_id = s.id
                AND t.status IN ('waiting', 'called')
            GROUP BY s.id, s.name
            ORDER BY ticket_count DESC, s.id
        """).fetchall()
    finally:
        connection.close()
    context = {
        "active_count": active["active_count"],
        "average_minutes": average["average_minutes"],
        "queue_statistics": queue_statistics,
        "service_statistics": service_statistics,
        "min_count": min_count, "error": error,
    }
    return render(request, "ticket_pages/statistics.html", context)
