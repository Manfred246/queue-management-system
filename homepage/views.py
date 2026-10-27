"""Главная страница и общая страница ошибки 404."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(request: HttpRequest) -> HttpResponse:
    """Показать главную страницу."""
    return render(request, "homepage/index.html")


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Показать шаблон ошибки для неизвестного URL."""
    return render(request, "404.html", status=404)
