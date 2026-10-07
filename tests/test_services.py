"""Проверки обработки коллекций и проверки входных данных."""

import pytest

from services import (
    add_service, filter_services, find_services, sort_services,
)
from users import add_user


def test_add_service(state):
    item = add_service(state["services"], " Выдача справок ", 5)
    assert item.id == 3
    assert item.name == "Выдача справок"


def test_search_ignores_case(state):
    assert find_services(state["services"], "КОНСУЛЬТ")[0].id == 1


def test_filter_skips_unavailable(state):
    state["services"][1].set_available(False)
    assert filter_services(state["services"], 10) == []


def test_sort_by_time(state):
    add_service(state["services"], "Быстрая услуга", 3)
    identifiers = [item.id for item in sort_services(state["services"])]
    assert identifiers == [3, 1, 2]


@pytest.mark.parametrize("minutes", [0, -1, True, "7"])
def test_bad_service_time(state, minutes):
    with pytest.raises(ValueError):
        add_service(state["services"], "Услуга", minutes)
    assert len(state["services"]) == 2


def test_blank_user_name(state):
    with pytest.raises(ValueError):
        add_user(state["users"], "   ")
