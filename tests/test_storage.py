"""Проверки сохранения, восстановления и повреждения JSON."""

import json

import pytest

from storage import load_state, save_state, state_to_data
from tickets import issue_ticket


def test_round_trip_and_continuing_number(state, issued, tmp_path):
    path = tmp_path / "state.json"
    save_state(state, path)
    restored = load_state(path)
    assert state_to_data(restored) == state_to_data(state)
    restored["tickets"][0].cancel()
    new = issue_ticket(restored["tickets"], restored["users"][1],
                       restored["services"][1], restored["queues"][1])
    assert new.number == 26


def test_missing_file_uses_initial_state(tmp_path):
    state = load_state(tmp_path / "missing.json")
    assert state["queues"][1].last_ticket_number == 24
    assert state["tickets"] == []


@pytest.mark.parametrize("content", ['{broken', '[]', '{}'])
def test_invalid_json_not_overwritten(tmp_path, content):
    path = tmp_path / "state.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        load_state(path)
    assert path.read_text(encoding="utf-8") == content


def test_broken_ticket_reference(state, issued, tmp_path):
    data = state_to_data(state)
    data["tickets"][0]["user_id"] = 999
    path = tmp_path / "state.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        load_state(path)


def test_failed_replace_keeps_previous_file(state, tmp_path, monkeypatch):
    from pathlib import Path

    path = tmp_path / "state.json"
    save_state(state, path)
    original = path.read_bytes()

    def fail_replace(*args):
        raise OSError("Запись запрещена")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError):
        save_state(state, path)
    assert path.read_bytes() == original
    assert list(tmp_path.glob("*.tmp")) == []


def test_load_rejects_broken_fifo_order(state, issued, tmp_path):
    second = issue_ticket(state["tickets"], state["users"][2],
                          state["services"][1], state["queues"][1])
    data = state_to_data(state)
    data["tickets"][1]["status"] = "called"
    path = tmp_path / "state.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError):
        load_state(path)
    assert second.status == "waiting"
