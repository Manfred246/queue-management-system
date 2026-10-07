"""Проверки пользовательского сценария и восстановления после ошибок."""

from main import main
from storage import load_state, save_state
from utils import input_int


def feed_input(monkeypatch, values):
    iterator = iter(values)
    monkeypatch.setattr("builtins.input", lambda prompt: next(iterator))


def test_numeric_input_retries(monkeypatch):
    feed_input(monkeypatch, ["буква", "-1", "3"])
    assert input_int("Количество: ") == 3


def test_menu_full_scenario(state, tmp_path, monkeypatch, capsys):
    path = tmp_path / "state.json"
    save_state(state, path)
    feed_input(monkeypatch, [
        "1", "2", "КОНСУЛЬТ", "3", "10", "4", "Справки", "5", "C",
        "5", "6", "3", "7", "8", "Оператор", "employee",
        "9", "1", "1", "1", "10", "12", "1", "13", "1",
        "9", "2", "1", "1", "11", "2", "14", "3", "0",
    ])
    main(path)
    restored = load_state(path)
    assert [item["status"] for item in restored["tickets"]] == [
        "completed", "cancelled",
    ]
    assert len(restored["services"]) == 3
    assert "Талон выдан" in capsys.readouterr().out


def test_menu_rejects_errors_and_preserves_state(
    state, tmp_path, monkeypatch, capsys,
):
    path = tmp_path / "state.json"
    save_state(state, path)
    feed_input(monkeypatch, [
        "bad", "9", "999", "4", "Повтор", "5", "A", "0",
    ])
    main(path)
    assert len(load_state(path)["services"]) == 2
    assert capsys.readouterr().out.count("Операция не выполнена") == 3


def test_menu_save_failure_rolls_back(state, tmp_path, monkeypatch, capsys):
    path = tmp_path / "state.json"
    save_state(state, path)

    def fail_save(*args):
        raise OSError("Нет доступа")

    monkeypatch.setattr("main.save_state", fail_save)
    feed_input(monkeypatch, ["8", "Новый", "visitor", "7", "0"])
    main(path)
    output = capsys.readouterr().out
    assert "3: Новый" not in output
    assert len(load_state(path)["users"]) == 2
