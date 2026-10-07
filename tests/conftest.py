"""Независимое состояние для каждого сценария проверки."""

import pytest

from storage import default_state
from users import add_user


@pytest.fixture
def state():
    result = default_state()
    add_user(result["users"], "Анна")
    add_user(result["users"], "Иван")
    return result


@pytest.fixture
def issued(state):
    from tickets import issue_ticket

    return issue_ticket(state["tickets"], state["users"][1],
                        state["services"][1], state["queues"][1])
