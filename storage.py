"""Загрузка и атомарное сохранение состояния в UTF-8 JSON."""

import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from validation import COLLECTIONS, validate_data

DATA_FILE = Path(__file__).resolve().parent / "data" / "state.json"


def default_state() -> dict:
    """Создать стартовые данные, продолжая настройки ПР1."""
    return {
        "users": {}, "tickets": [],
        "services": {
            1: {"id": 1, "name": "Консультация",
                "average_service_time": 7, "is_available": True},
            2: {"id": 2, "name": "Оформление документов",
                "average_service_time": 12, "is_available": True},
        },
        "queues": {
            1: {"id": 1, "name": "Основная очередь", "service_id": 1,
                "prefix": "A", "is_open": True, "last_ticket_number": 24},
            2: {"id": 2, "name": "Очередь документов", "service_id": 2,
                "prefix": "B", "is_open": True, "last_ticket_number": 0},
        },
    }


def state_to_data(state: dict) -> dict:
    """Подготовить коллекции к записи без целочисленных ключей JSON."""
    return {name: state[name] if name == "tickets"
            else list(state[name].values()) for name in COLLECTIONS}


def load_state(filename: Path = DATA_FILE) -> dict:
    """Прочитать данные; при отсутствии файла создать начальное состояние."""
    try:
        with Path(filename).open(encoding="utf-8") as stream:
            data = json.load(stream)
    except FileNotFoundError:
        return default_state()
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError(f"Не удалось прочитать JSON: {error}") from error
    try:
        validate_data(data)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f"Некорректные данные JSON: {error}") from error
    return {name: data[name] if name == "tickets"
            else {item["id"]: item for item in data[name]}
            for name in COLLECTIONS}


def save_state(state: dict, filename: Path = DATA_FILE) -> None:
    """Заменить файл целиком только после успешной записи всех данных."""
    data = state_to_data(state)
    validate_data(data)
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
