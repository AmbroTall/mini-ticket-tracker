from django.urls import path

from tickets.views import health

urlpatterns = [
    path("health", health, name="health"),
]
