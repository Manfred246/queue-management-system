"""Корневые маршруты проекта."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("services/", include("catalog.urls")),
    path("queues/", include("catalog.queue_urls")),
    path("tickets/", include("ticket_pages.urls")),
]

handler404 = "homepage.views.page_not_found"
