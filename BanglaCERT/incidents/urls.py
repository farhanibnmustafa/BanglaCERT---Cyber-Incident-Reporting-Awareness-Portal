from django.urls import path

from . import views

app_name = "incidents"

urlpatterns = [
    path("report/", views.public_report_incident, name="report"),
    path("report/success/", views.public_report_success, name="report_success"),
]
