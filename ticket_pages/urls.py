"""Маршруты талонов."""

from django.urls import path

from . import views

app_name = "tickets"

urlpatterns = [
    path("", views.tickets, name="tickets"),
    path("statistics/", views.statistics, name="statistics"),
    path("<int:ticket_id>/", views.ticket_detail, name="ticket_detail"),
]
