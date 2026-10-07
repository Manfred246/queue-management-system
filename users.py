"""Пользователь и функции обработки коллекции пользователей."""

from utils import next_id, require_int, require_text


class User:
    """Посетитель или сотрудник системы электронной очереди."""

    def __init__(
        self, user_id: int, name: str, role: str = "visitor",
    ) -> None:
        if role not in ("visitor", "employee"):
            raise ValueError("Неизвестная роль пользователя.")
        self.id = require_int(user_id)
        self.name = require_text(name)
        self.role = role

    def can_receive_ticket(self) -> bool:
        """Проверить, является ли пользователь посетителем."""
        return self.role == "visitor"

    def __str__(self) -> str:
        role = "посетитель" if self.can_receive_ticket() else "сотрудник"
        return f"{self.id}: {self.name}, {role}"


def add_user(
    users: dict[int, User], name: str, role: str = "visitor",
) -> User:
    """Создать пользователя и добавить объект в коллекцию."""
    user = User(next_id(users), name, role)
    users[user.id] = user
    return user
