"""Функции работы с посетителями и сотрудниками."""

from utils import next_id, require_text


def add_user(users: dict, name: str, role: str = "visitor") -> dict:
    """Добавить пользователя с ролью посетителя или сотрудника."""
    if role not in ("visitor", "employee"):
        raise ValueError("Неизвестная роль пользователя.")
    user = {"id": next_id(users), "name": require_text(name), "role": role}
    users[user["id"]] = user
    return user
