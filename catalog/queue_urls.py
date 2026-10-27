"""Маршруты очередей из каталога."""

from django.urls import path

from . import views

app_name = "queues"

urlpatterns = [
    path("", views.queues, name="queues"),
    path("available/", views.available_queues, name="available"),
    path("<int:queue_id>/", views.queue_detail, name="queue_detail"),
]
