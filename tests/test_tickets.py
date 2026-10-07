"""Проверки жизненного цикла талона и очередности обслуживания."""

import pytest

from tickets import (
    calculate_wait_time, get_ticket_status, issue_ticket,
)
from users import add_user


def issue(state, user_id=2, service_id=1, queue_id=1):
    return issue_ticket(
        state["tickets"], state["users"][user_id],
        state["services"][service_id], state["queues"][queue_id],
    )


def test_number_and_waiting_position(state, issued):
    second = issue(state)
    assert (issued.number, second.number) == (25, 26)
    assert second.position(state["tickets"]) == 1
    assert calculate_wait_time(1, 7) == 7
    assert get_ticket_status(0) == "Вы следующий"


def test_closed_queue_rejects_ticket(state):
    state["queues"][1].set_open(False)
    with pytest.raises(ValueError):
        issue(state)
    assert state["tickets"] == []
    assert state["queues"][1].last_ticket_number == 24


def test_unavailable_service_rejects_ticket(state):
    state["services"][1].set_available(False)
    with pytest.raises(ValueError):
        issue(state)


def test_queue_service_mismatch(state):
    with pytest.raises(ValueError):
        issue(state, service_id=2)


def test_employee_cannot_receive_ticket(state):
    employee = add_user(state["users"], "Оператор", "employee")
    with pytest.raises(ValueError):
        issue(state, user_id=employee.id)


def test_duplicate_active_ticket_forbidden(state, issued):
    with pytest.raises(ValueError):
        issue(state, user_id=1)
    assert len(state["tickets"]) == 1


def test_cancel_preserves_history_and_allows_new_ticket(state, issued):
    issued.cancel()
    new = issue(state, user_id=1)
    assert issued.status == "cancelled"
    assert new.number == 26
    assert len(state["tickets"]) == 2


def test_fifo_skips_cancelled_tickets(state, issued):
    second = issue(state)
    issued.cancel()
    assert state["queues"][1].call_next(state["tickets"]) is second


def test_only_one_called_ticket(state, issued):
    issue(state)
    state["queues"][1].call_next(state["tickets"])
    with pytest.raises(ValueError):
        state["queues"][1].call_next(state["tickets"])


def test_complete_then_call_next(state, issued):
    second = issue(state)
    state["queues"][1].call_next(state["tickets"])
    issued.complete()
    assert state["queues"][1].call_next(state["tickets"]) is second
    assert issued.status == "completed"


def test_cannot_complete_waiting_ticket(state, issued):
    with pytest.raises(ValueError):
        issued.complete()


def test_empty_queue(state):
    with pytest.raises(ValueError):
        state["queues"][1].call_next(state["tickets"])


def test_queues_are_independent(state, issued):
    other = issue(state, user_id=1, service_id=2, queue_id=2)
    assert other.number == 1
    assert other.position(state["tickets"]) == 0
    assert state["queues"][2].call_next(state["tickets"]) is other
