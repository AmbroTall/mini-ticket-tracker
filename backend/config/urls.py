from django.urls import include, path

from tickets.views import health

urlpatterns = [
    path("health", health, name="health"),
    path("", include("tickets.urls")),
]
