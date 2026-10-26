"""Маршруты очередей из каталога."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.queues, name="queues"),
    path("<int:queue_id>/", views.queue_detail, name="queue_detail"),
]
