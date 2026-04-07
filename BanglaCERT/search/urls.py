from django.urls import path
from . import views

app_name = "search"

urlpatterns = [
    path("", views.incident_search, name="index"),
]
