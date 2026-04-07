from django.urls import path

from . import views

app_name = "incidents"

urlpatterns = [
    path("", views.home, name="home"),
    path("report/", views.report_incident, name="report"),
    path("public-report/", views.public_report_incident, name="public_report"),
    path("public-report/success/", views.public_report_success, name="public_report_success"),
    path("public-report/status/", views.public_report_status, name="public_report_status"),
    path("mine/", views.my_incidents, name="my_incidents"),
    path("<int:incident_id>/", views.incident_detail, name="detail"),
    path("<int:incident_id>/comment/", views.add_comment, name="add_comment"),
]
