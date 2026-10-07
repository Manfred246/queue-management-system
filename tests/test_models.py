"""Проверки объектной модели и совместимости с JSON этапа ПР2."""

import pytest

from queues import Queue, add_queue, can_issue_ticket, create_ticket_number
from services import Service
from storage import data_to_state, load_state, save_state, state_to_data
from tickets import Ticket
from users import User


def test_ticket_composes_shared_objects(state, issued):
    assert isinstance(issued, Ticket)
    assert issued.user is state["users"][1]
    assert issued.queue is state["queues"][1]
    assert issued.service is state["services"][1]
    assert issued.queue.service is issued.service


def test_load_restores_shared_references(state, issued, tmp_path):
    path = tmp_path / "state.json"
    save_state(state, path)
    restored = load_state(path)
    ticket = restored["tickets"][0]
    assert ticket.user is restored["users"][1]
    assert ticket.queue is restored["queues"][1]
    assert ticket.service is restored["services"][1]
    assert ticket.queue.service is ticket.service


def test_method_updates_referenced_service(state, issued):
    state["services"][1].set_available(False)
    assert not issued.service.is_available
    assert not issued.queue.can_issue_ticket()


@pytest.mark.parametrize("attribute,value", [
    ("status", "completed"), ("is_active", False),
])
def test_ticket_state_cannot_be_assigned(issued, attribute, value):
    with pytest.raises(AttributeError):
        setattr(issued, attribute, value)
    assert issued.status == "waiting"


def test_invalid_status_transition_does_not_change_ticket(issued):
    issued.cancel()
    with pytest.raises(ValueError):
        issued.complete()
    with pytest.raises(ValueError):
        issued.cancel()
    assert issued.status == "cancelled"


def test_methods_calculate_dynamic_wait(state, issued):
    from tickets import issue_ticket

    second = issue_ticket(state["tickets"], state["users"][2],
                          state["services"][1], state["queues"][1])
    assert second.position(state["tickets"]) == 1
    assert second.wait_time(state["tickets"]) == 7
    issued.cancel()
    assert second.position(state["tickets"]) == 0
    assert second.wait_time(state["tickets"]) == 0


def test_cannot_call_later_ticket_directly(state, issued):
    from tickets import issue_ticket

    second = issue_ticket(state["tickets"], state["users"][2],
                          state["services"][1], state["queues"][1])
    with pytest.raises(ValueError):
        second.call(state["tickets"])
    assert second.status == "waiting"


def test_polymorphic_string_representation(state, issued):
    objects = [state["users"][1], state["services"][1],
               state["queues"][1], issued]
    strings = [str(item) for item in objects]
    assert all(isinstance(item, str) for item in strings)
    assert "Анна" in strings[0]
    assert "Консультация" in strings[1]
    assert "Основная очередь" in strings[2]
    assert "A25" in strings[3]


def test_legacy_pr2_json_loads_without_migration():
    data = {
        "users": [{"id": 1, "name": "Посетитель", "role": "visitor"}],
        "services": [{"id": 1, "name": "Консультация",
                      "average_service_time": 7, "is_available": True}],
        "queues": [{"id": 1, "name": "Основная очередь", "service_id": 1,
                    "prefix": "A", "is_open": False,
                    "last_ticket_number": 25}],
        "tickets": [{"id": 1, "number": 25, "user_id": 1, "service_id": 1,
                     "queue_id": 1, "status": "cancelled",
                     "issued_at": "2026-10-07T12:00:00"}],
    }
    restored = data_to_state(data)
    assert isinstance(restored["users"][1], User)
    assert isinstance(restored["services"][1], Service)
    assert isinstance(restored["queues"][1], Queue)
    assert restored["tickets"][0].status == "cancelled"
    assert state_to_data(restored) == data


def test_queue_rejects_duplicate_prefix(state):
    with pytest.raises(ValueError):
        add_queue(state["queues"], state["services"][1], "Повтор", "A")
    assert len(state["queues"]) == 2


def test_original_number_and_availability_functions():
    assert create_ticket_number(24) == 25
    assert can_issue_ticket(True, True)
    assert not can_issue_ticket(False, True)


def test_ticket_rejects_service_from_another_queue(state):
    with pytest.raises(ValueError):
        Ticket(1, 25, state["users"][1], state["services"][2],
               state["queues"][1])
