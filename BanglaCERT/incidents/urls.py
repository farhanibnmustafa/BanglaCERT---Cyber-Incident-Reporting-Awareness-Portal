from django.urls import path

from . import views

app_name = "incidents"

urlpatterns = [
    path("", views.home, name="home"),
    path("report/", views.report_incident, name="report"),
    path("mine/", views.my_incidents, name="my_incidents"),
    path("<int:incident_id>/", views.incident_detail, name="detail"),
    path("<int:incident_id>/comment/", views.add_comment, name="add_comment"),
]
