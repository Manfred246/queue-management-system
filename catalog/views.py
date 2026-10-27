"""Получение услуг и очередей из SQLite для страниц сайта."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.database import get_connection


def services(request: HttpRequest) -> HttpResponse:
    """Показать услуги; при необходимости ограничить время обслуживания."""
    max_minutes = request.GET.get("max_minutes", "")
    error = ""
    services_data = []
    connection = get_connection()
    try:
        if max_minutes:
            try:
                minutes = int(max_minutes)
                if minutes < 1:
                    raise ValueError
            except ValueError:
                error = "Введите положительное целое число минут."
            else:
                services_data = connection.execute("""
                    SELECT id, name, average_service_time, is_available
                    FROM services
                    WHERE average_service_time <= ?
                    ORDER BY average_service_time, id
                """, (minutes,)).fetchall()
        else:
            services_data = connection.execute("""
                SELECT id, name, average_service_time, is_available
                FROM services
                ORDER BY name, id
            """).fetchall()
    finally:
        connection.close()
    context = {
        "services": services_data, "max_minutes": max_minutes, "error": error,
    }
    return render(request, "catalog/service_list.html", context)


def service_detail(request: HttpRequest, service_id: int) -> HttpResponse:
    """Показать услугу и связанные очереди или вернуть 404."""
    connection = get_connection()
    try:
        service = connection.execute("""
            SELECT id, name, average_service_time, is_available
            FROM services WHERE id = ?
        """, (service_id,)).fetchone()
        service_queues = connection.execute("""
            SELECT id, name FROM queues
            WHERE service_id = ? ORDER BY name, id
        """, (service_id,)).fetchall()
    finally:
        connection.close()
    context = {"service": service, "queues": service_queues}
    return render(
        request, "catalog/service_detail.html", context,
        status=404 if service is None else 200,
    )


def queues(request: HttpRequest) -> HttpResponse:
    """Показать очереди с названиями связанных услуг."""
    connection = get_connection()
    try:
        queues_data = connection.execute("""
            SELECT q.id, q.name, q.is_open, s.name AS service_name
            FROM queues AS q
            JOIN services AS s ON q.service_id = s.id
            ORDER BY q.name, q.id
        """).fetchall()
    finally:
        connection.close()
    return render(request, "catalog/queue_list.html", {"queues": queues_data})


def queue_detail(request: HttpRequest, queue_id: int) -> HttpResponse:
    """Показать очередь, доступность выдачи и число активных талонов."""
    connection = get_connection()
    try:
        queue = connection.execute("""
            SELECT q.id, q.name, q.service_id, q.is_open,
                   s.name AS service_name,
                   (q.is_open AND s.is_available) AS can_issue_ticket,
                   (SELECT COUNT(*) FROM tickets AS t
                    WHERE t.queue_id = q.id
                      AND t.status IN ('waiting', 'called')) AS active_count
            FROM queues AS q
            JOIN services AS s ON q.service_id = s.id
            WHERE q.id = ?
        """, (queue_id,)).fetchone()
    finally:
        connection.close()
    return render(
        request, "catalog/queue_detail.html", {"queue": queue},
        status=404 if queue is None else 200,
    )


def available_queues(request: HttpRequest) -> HttpResponse:
    """Найти очереди, в которые посетитель может получить талон."""
    user_id = request.GET.get("user_id", "")
    user = None
    queues_data = []
    error = ""
    if user_id:
        try:
            selected_id = int(user_id)
            if selected_id < 1:
                raise ValueError
        except ValueError:
            error = "Введите положительный целый ID посетителя."
        else:
            connection = get_connection()
            try:
                user = connection.execute("""
                    SELECT id, name, role FROM users WHERE id = ?
                """, (selected_id,)).fetchone()
                if user is None:
                    error = "Пользователь не найден."
                elif user["role"] != "visitor":
                    error = "Талоны выдаются только посетителям."
                else:
                    queues_data = connection.execute("""
                        SELECT q.id, q.name, s.name AS service_name
                        FROM queues AS q
                        JOIN services AS s ON q.service_id = s.id
                        WHERE q.is_open = 1 AND s.is_available = 1
                          AND q.id NOT IN (
                              SELECT queue_id FROM tickets
                              WHERE user_id = ?
                                AND status IN ('waiting', 'called')
                          )
                        ORDER BY q.name, q.id
                    """, (selected_id,)).fetchall()
            finally:
                connection.close()
    context = {
        "queues": queues_data, "user": user,
        "user_id": user_id, "error": error,
    }
    return render(request, "catalog/available.html", context)
