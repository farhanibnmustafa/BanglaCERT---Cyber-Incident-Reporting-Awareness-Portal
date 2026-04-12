from django.urls import path

from incidents import staff_views

app_name = "admin"

urlpatterns = [
    path("setup/", staff_views.setup_first_admin, name="setup"),
    path("", staff_views.dashboard, name="index"),
    path("staff/", staff_views.staff_accounts, name="staff_accounts"),
    path("incidents/<int:incident_id>/", staff_views.incident_detail, name="incident_detail"),
    path("incidents/<int:incident_id>/category/", staff_views.update_incident_category, name="incident_category"),
    path("incidents/<int:incident_id>/status/", staff_views.update_incident_status, name="incident_status"),
    path("incidents/<int:incident_id>/comments/", staff_views.add_incident_comment, name="incident_comment"),
    path("incidents/<int:incident_id>/inline-update/", staff_views.inline_update_incident, name="incident_inline_update"),
    path("incidents/<int:incident_id>/resend-email/", staff_views.resend_incident_email, name="incident_resend_email"),
    # Staff Management
    path("staff/<int:user_id>/active/", staff_views.toggle_staff_active, name="toggle_staff_active"),
    path("staff/<int:user_id>/remove/", staff_views.remove_staff_access, name="remove_staff_access"),
    path("staff/<int:user_id>/edit/", staff_views.edit_staff_user, name="edit_staff"),
]
