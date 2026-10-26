"""Маршруты талонов."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.tickets, name="tickets"),
    path("<int:ticket_id>/", views.ticket_detail, name="ticket_detail"),
]
