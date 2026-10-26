"""Главная страница, общий HTML-каркас и обработчик 404."""

from html import escape

from django.http import HttpRequest, HttpResponse


def page(title: str, content: str) -> str:
    """Собрать HTML-документ с общим оформлением и навигацией."""
    bootstrap = (
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3"
        "/dist/css/bootstrap.min.css"
    )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title)}</title>
    <link rel="stylesheet" href="{bootstrap}">
    <style>
        body {{ background: #f5f6f8; }}
        main {{ padding-top: 24px; padding-bottom: 24px; }}
        h1 {{ margin-bottom: 20px; }}
    </style>
</head>
<body>
    <nav class="nav bg-white border-bottom p-3">
        <a class="nav-link" href="/">Главная</a>
        <a class="nav-link" href="/services/">Услуги</a>
        <a class="nav-link" href="/queues/">Очереди</a>
        <a class="nav-link" href="/tickets/">Талоны</a>
    </nav>
    <main class="container">{content}</main>
</body>
</html>"""


def index(request: HttpRequest) -> HttpResponse:
    """Показать описание проекта и ссылки на его разделы."""
    content = """
    <h1>Система управления очередью</h1>
    <p class="lead">Услуги, очереди и талоны посетителей.</p>
    <p>Выберите раздел для просмотра данных.</p>
    <a class="btn btn-primary me-2" href="/services/">Услуги</a>
    <a class="btn btn-secondary me-2" href="/queues/">Очереди</a>
    <a class="btn btn-outline-primary" href="/tickets/">Талоны</a>
    """
    return HttpResponse(page("Система управления очередью", content))


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Вернуть общую страницу ошибки для неизвестного адреса."""
    content = """
    <h1 class="text-danger">404 — страница не найдена</h1>
    <p>Проверьте адрес или вернитесь на главную.</p>
    <a class="btn btn-primary" href="/">На главную</a>
    """
    return HttpResponse(page("Страница не найдена", content), status=404)
