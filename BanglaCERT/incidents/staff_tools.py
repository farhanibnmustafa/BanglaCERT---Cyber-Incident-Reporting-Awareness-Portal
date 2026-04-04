from django.contrib.auth import get_user_model
from django.utils import timezone

from auditlog.models import AuditLog
from notifications.services import notify_incident_status_change_with_reason

from .models import Incident


User = get_user_model()
INCIDENT_MANAGER_USERNAME = "systemadmin40329"


def is_incident_manager(user):
    return user.is_authenticated and user.username == INCIDENT_MANAGER_USERNAME


def has_staff_users():
    return User.objects.filter(is_staff=True).exists()


def can_manage_staff_users(user):
    return user.is_authenticated and user.is_staff and (user.is_superuser or is_incident_manager(user))


def log_staff_action(user, action, incident, message=""):
    AuditLog.objects.create(
        user=user,
        action=action,
        object_type="Incident",
        object_id=incident.id,
        message=message,
    )


def get_status_action(new_status):
    if new_status == Incident.STATUS_VERIFIED:
        return AuditLog.ACTION_APPROVE
    if new_status == Incident.STATUS_REJECTED:
        return AuditLog.ACTION_REJECT
    if new_status == Incident.STATUS_UNDER_REVIEW:
        return AuditLog.ACTION_UNDER_REVIEW
    if new_status == Incident.STATUS_NEEDS_CLARIFICATION:
        return AuditLog.ACTION_REQUEST_CLARIFICATION
    return AuditLog.ACTION_UPDATE


def get_status_label(status_value):
    return dict(Incident.STATUS_CHOICES).get(status_value, status_value)


def get_actor_context(user):
    changed_by = user.username if user else "Unknown"
    changed_at = timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M:%S %Z")
    return changed_by, changed_at


def build_audit_message(user, detail):
    changed_by, changed_at = get_actor_context(user)
    return f"{detail} by {changed_by} at {changed_at}."


def build_status_change_message(user, previous_status, new_status):
    return build_audit_message(
        user,
        (
            f"Status changed from {get_status_label(previous_status)} "
            f"to {get_status_label(new_status)}"
        ),
    )


def log_status_change(user, incident, previous_status, new_status):
    action = get_status_action(new_status)
    message = build_status_change_message(user, previous_status, new_status)
    log_staff_action(user, action, incident, message)


def notify_status_change(incident, previous_status, new_status):
    return notify_incident_status_change_with_reason(
        incident=incident,
        previous_status=previous_status,
        new_status=new_status,
    )
