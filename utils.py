"""Проверки значений и безопасный консольный ввод."""


def require_int(value: int, minimum: int = 1) -> int:
    """Проверить целое число, исключая логические значения."""
    if type(value) is not int or value < minimum:
        raise ValueError(f"Ожидается целое число не меньше {minimum}.")
    return value


def require_text(value: str) -> str:
    """Проверить непустую строку и убрать внешние пробелы."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Название или имя не может быть пустым.")
    return value.strip()


def require_bool(value: bool) -> bool:
    """Проверить логическое значение из JSON."""
    if type(value) is not bool:
        raise ValueError("Ожидается логическое значение.")
    return value


def input_int(prompt: str, minimum: int = 1) -> int:
    """Повторять ввод до получения допустимого целого числа."""
    while True:
        try:
            return require_int(int(input(prompt)), minimum)
        except ValueError as error:
            print(f"Ошибка ввода: {error}")


def input_text(prompt: str) -> str:
    """Повторять ввод до получения непустой строки."""
    while True:
        try:
            return require_text(input(prompt))
        except ValueError as error:
            print(f"Ошибка ввода: {error}")


def next_id(records: dict) -> int:
    """Получить свободный идентификатор коллекции."""
    return max(records, default=0) + 1
