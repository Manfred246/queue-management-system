"""Проверки переноса данных и SQL-сценариев на временной базе."""

import json
import os
import sqlite3

import django
import pytest
from django.test import Client

from db.database import create_tables, get_connection
from db.import_json import import_data
from storage import state_to_data
from tickets import issue_ticket
from users import add_user

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "queue_site.settings")
django.setup()


@pytest.fixture
def sql_source(tmp_path, state):
    add_user(state["users"], "Сотрудник", "employee")
    issue_ticket(state["tickets"], state["users"][1],
                 state["services"][1], state["queues"][1])
    cancelled = issue_ticket(state["tickets"], state["users"][2],
                             state["services"][1], state["queues"][1])
    cancelled.cancel()
    completed = issue_ticket(state["tickets"], state["users"][1],
                             state["services"][2], state["queues"][2])
    completed.call(state["tickets"])
    completed.complete()
    path = tmp_path / "source.json"
    path.write_text(json.dumps(state_to_data(state)), encoding="utf-8")
    return path


@pytest.fixture
def database(tmp_path, sql_source):
    path = tmp_path / "queue.sqlite"
    create_tables(path)
    import_data(sql_source, path)
    return path


def test_import_preserves_records_and_links(database, sql_source):
    create_tables(database)  # Повторное применение схемы не стирает данные.
    source = json.loads(sql_source.read_text(encoding="utf-8"))
    connection = get_connection(database)
    try:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        for table in ("users", "services", "queues", "tickets"):
            # Имена таблиц заданы в тесте, не приходят от пользователя.
            rows = connection.execute("SELECT * FROM " + table).fetchall()
            assert len(rows) == len(source[table])
        row = connection.execute("""
            SELECT u.name, s.name AS service_name FROM tickets AS t
            JOIN users AS u ON t.user_id = u.id
            JOIN services AS s ON t.service_id = s.id WHERE t.id = 1
        """).fetchone()
        assert row["name"] == "Анна"
        assert row["service_name"] == "Консультация"
    finally:
        connection.close()


def test_import_rolls_back_partial_inserts(tmp_path, sql_source):
    path = tmp_path / "conflict.sqlite"
    create_tables(path)
    connection = get_connection(path)
    try:
        connection.execute("""
            INSERT INTO services (id, name, average_service_time)
            VALUES (2, 'Исходная услуга', 5)
        """)
        connection.commit()
    finally:
        connection.close()
    with pytest.raises(sqlite3.IntegrityError):
        import_data(sql_source, path)
    connection = get_connection(path)
    try:
        count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        assert count == 0
        rows = connection.execute("SELECT id, name FROM services").fetchall()
        assert [tuple(row) for row in rows] == [(2, "Исходная услуга")]
    finally:
        connection.close()


def test_foreign_key_rejects_unknown_service(database):
    connection = get_connection(database)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("""
                INSERT INTO queues (id, name, service_id, prefix)
                VALUES (99, 'Ошибка', 9999, 'X')
            """)
    finally:
        connection.close()


@pytest.fixture
def web_client(database, monkeypatch):
    from catalog import views as catalog_views
    from ticket_pages import views as ticket_views

    def connect():
        return get_connection(database)

    monkeypatch.setattr(catalog_views, "get_connection", connect)
    monkeypatch.setattr(ticket_views, "get_connection", connect)
    return Client(HTTP_HOST="127.0.0.1")


def test_service_filter_and_invalid_input(web_client):
    body = web_client.get("/services/?max_minutes=7").content.decode()
    assert "Консультация" in body
    assert "Оформление документов" not in body
    body = web_client.get("/services/?max_minutes=1").content.decode()
    assert "Услуги не найдены." in body
    body = web_client.get("/services/?max_minutes=abc").content.decode()
    assert "Введите положительное целое число минут." in body


def test_ticket_states_and_join(web_client):
    active = web_client.get("/tickets/").content.decode()
    assert "A25" in active and "A26" not in active and "B1" not in active
    history = web_client.get("/tickets/?state=all").content.decode()
    assert "A25" in history and "A26" in history and "B1" in history
    cancelled = web_client.get("/tickets/?state=cancelled").content.decode()
    assert "A26" in cancelled and "A25" not in cancelled
    detail = web_client.get("/tickets/1/").content.decode()
    assert "Анна" in detail and "Консультация" in detail
    assert "Основная очередь" in detail


def test_available_queues_exclude_active_closed_and_employees(
    web_client, database,
):
    body = web_client.get("/queues/available/?user_id=1").content.decode()
    assert "Очередь документов" in body and "Основная очередь" not in body
    connection = get_connection(database)
    try:
        connection.execute("UPDATE queues SET is_open = 0 WHERE id = 2")
        connection.commit()
    finally:
        connection.close()
    body = web_client.get("/queues/available/?user_id=1").content.decode()
    assert "Доступных очередей нет." in body
    body = web_client.get("/queues/available/?user_id=3").content.decode()
    assert "Талоны выдаются только посетителям." in body
    body = web_client.get("/queues/available/?user_id=9999").content.decode()
    assert "Пользователь не найден." in body


def test_statistics_keep_zero_groups_and_filter_having(web_client):
    body = web_client.get("/tickets/statistics/").content.decode()
    assert "Активных талонов: 1" in body
    assert "Очередь документов" in body and "активных талонов: 0" in body
    body = web_client.get("/tickets/statistics/?min_count=2").content.decode()
    assert "Очередей с такой нагрузкой нет." in body


def test_waiting_time_ignores_cancelled_and_completed(web_client, database):
    connection = get_connection(database)
    try:
        connection.execute("""
            INSERT INTO tickets
                (id, number, user_id, service_id, queue_id, issued_at)
            VALUES (4, 27, 2, 1, 1, '2026-10-27T12:00:00')
        """)
        connection.commit()
    finally:
        connection.close()
    body = web_client.get("/tickets/4/").content.decode()
    assert "Ожидание: 7 мин." in body


@pytest.mark.parametrize("url", [
    "/services/9999/", "/queues/9999/", "/tickets/9999/", "/services/abc/",
])
def test_missing_resource_returns_404(web_client, url):
    assert web_client.get(url).status_code == 404
