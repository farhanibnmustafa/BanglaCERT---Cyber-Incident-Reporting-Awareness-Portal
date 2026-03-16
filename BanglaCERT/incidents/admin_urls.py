from django.urls import path

from . import staff_views

app_name = "admin"

urlpatterns = [
    path("setup/", staff_views.setup_first_admin, name="setup"),
    path("", staff_views.dashboard, name="index"),
    path("staff/", staff_views.staff_accounts, name="staff_accounts"),
    path("incidents/<int:incident_id>/", staff_views.incident_detail, name="incident_detail"),
    path("incidents/<int:incident_id>/category/", staff_views.update_incident_category, name="incident_category"),
    path("incidents/<int:incident_id>/status/", staff_views.update_incident_status, name="incident_status"),
    path("incidents/<int:incident_id>/comments/", staff_views.add_incident_comment, name="incident_comment"),
]
