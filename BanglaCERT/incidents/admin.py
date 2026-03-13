from django import forms
from django.contrib import admin, messages
from django.utils import timezone
from django.utils.html import format_html, format_html_join

from auditlog.models import AuditLog
from notifications.services import notify_incident_status_change_with_reason

from .models import Incident


INCIDENT_MANAGER_USERNAME = "systemadmin40329"


def is_incident_manager(user):
    return user.is_authenticated and user.username == INCIDENT_MANAGER_USERNAME


def log_admin_action(user, action, incident, message=""):
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
    log_admin_action(user, action, incident, message)


def notify_status_change(incident, previous_status, new_status):
    return notify_incident_status_change_with_reason(
        incident=incident,
        previous_status=previous_status,
        new_status=new_status,
    )


@admin.action(description="Approve selected incidents")
def approve_incidents(modeladmin, request, queryset):
    for incident in queryset:
        previous_status = incident.status
        incident.status = Incident.STATUS_VERIFIED
        incident.save(update_fields=["status", "updated_at"])
        log_status_change(request.user, incident, previous_status, incident.status)
        sent, reason = notify_status_change(incident, previous_status, incident.status)
        if not sent:
            modeladmin.message_user(
                request,
                f"Status email not sent for Incident #{incident.id}: {reason}",
                level=messages.WARNING,
            )


@admin.action(description="Mark selected incidents as Under Review")
def mark_under_review(modeladmin, request, queryset):
    for incident in queryset:
        previous_status = incident.status
        incident.status = Incident.STATUS_UNDER_REVIEW
        incident.save(update_fields=["status", "updated_at"])
        log_status_change(request.user, incident, previous_status, incident.status)
        sent, reason = notify_status_change(incident, previous_status, incident.status)
        if not sent:
            modeladmin.message_user(
                request,
                f"Status email not sent for Incident #{incident.id}: {reason}",
                level=messages.WARNING,
            )


@admin.action(description="Reject selected incidents")
def reject_incidents(modeladmin, request, queryset):
    for incident in queryset:
        previous_status = incident.status
        incident.status = Incident.STATUS_REJECTED
        incident.save(update_fields=["status", "updated_at"])
        log_status_change(request.user, incident, previous_status, incident.status)
        sent, reason = notify_status_change(incident, previous_status, incident.status)
        if not sent:
            modeladmin.message_user(
                request,
                f"Status email not sent for Incident #{incident.id}: {reason}",
                level=messages.WARNING,
            )


class IncidentAdminForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = "__all__"
        widgets = {
            "incident_date": forms.DateInput(attrs={"type": "date"}),
        }


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    form = IncidentAdminForm
    list_display = ("id", "title", "created_at", "status", "is_anonymous", "submitted_by")
    list_display_links = ("id", "title")
    list_editable = ("status",)
    list_filter = ("status", "category", "is_anonymous")
    search_fields = ("title", "description")
    actions = None
    actions_on_top = False
    actions_on_bottom = False

    def get_fields(self, request, obj=None):
        base_fields = ("title", "category", "description", "incident_date", "is_anonymous")
        if obj is None:
            # On create: hide status + created_by fields
            return base_fields
        # On view/edit: show status + created_by
        return base_fields + ("status", "created_by", "created_at", "updated_at", "audit_log_entries")

    def get_readonly_fields(self, request, obj=None):
        readonly = ["audit_log_entries"]
        # On edit, lock core incident details and metadata.
        if obj:
            readonly.extend(
                [
                    "title",
                    "description",
                    "incident_date",
                    "is_anonymous",
                    "created_by",
                    "created_at",
                    "updated_at",
                ]
            )
        return readonly

    def submitted_by(self, obj):
        return obj.reporter_display_name

    submitted_by.short_description = "Submitted by"

    def has_add_permission(self, request):
        # Incident creation is disabled in admin for all users.
        return False

    def has_change_permission(self, request, obj=None):
        # Any staff can change incidents (including incidentadmin229)
        return request.user.is_authenticated and request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        # Only systemadmin40329 can delete incidents
        return is_incident_manager(request.user)

    def has_view_permission(self, request, obj=None):
        # Any staff can view incidents
        return request.user.is_authenticated and request.user.is_staff

    def audit_log_entries(self, obj):
        if not obj:
            return "-"
        logs = (
            AuditLog.objects.filter(object_type="Incident", object_id=obj.id)
            .order_by("-created_at")
            .select_related("user")[:20]
        )
        if not logs:
            return "No audit log entries yet."
        items = format_html_join(
            "",
            "<li>{} — <strong>{}</strong> by {}<br><span style='color:#667085'>{}</span></li>",
            (
                (
                    timezone.localtime(log.created_at).strftime("%Y-%m-%d %H:%M:%S %Z"),
                    log.get_action_display(),
                    log.user.username if log.user else "Unknown",
                    log.message or "",
                )
                for log in logs
            ),
        )
        return format_html("<ul style='margin:0; padding-left:18px'>{}</ul>", items)

    audit_log_entries.short_description = "Audit log"

    def save_model(self, request, obj, form, change):
        previous_status = None
        if change and obj.pk:
            previous_status = Incident.objects.filter(pk=obj.pk).values_list("status", flat=True).first()
        if not change and not obj.created_by and request.user.is_authenticated and not obj.is_anonymous:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        if not change:
            log_admin_action(
                request.user,
                AuditLog.ACTION_CREATE,
                obj,
                build_audit_message(request.user, "Incident created"),
            )
            return

        if previous_status and previous_status != obj.status:
            log_status_change(request.user, obj, previous_status, obj.status)
            sent, reason = notify_status_change(obj, previous_status, obj.status)
            if not sent:
                self.message_user(
                    request,
                    f"Status email not sent for Incident #{obj.id}: {reason}",
                    level=messages.WARNING,
                )
        else:
            log_admin_action(
                request.user,
                AuditLog.ACTION_UPDATE,
                obj,
                build_audit_message(request.user, "Incident updated"),
            )
