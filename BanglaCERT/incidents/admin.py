from django import forms
from django.contrib import admin
from django.utils.html import format_html, format_html_join

from auditlog.models import AuditLog

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


@admin.action(description="Approve selected incidents")
def approve_incidents(modeladmin, request, queryset):
    for incident in queryset:
        incident.status = Incident.STATUS_VERIFIED
        incident.save(update_fields=["status", "updated_at"])
        log_admin_action(request.user, AuditLog.ACTION_APPROVE, incident, "Approved by admin.")


@admin.action(description="Mark selected incidents as Under Review")
def mark_under_review(modeladmin, request, queryset):
    for incident in queryset:
        incident.status = Incident.STATUS_UNDER_REVIEW
        incident.save(update_fields=["status", "updated_at"])
        log_admin_action(request.user, AuditLog.ACTION_UNDER_REVIEW, incident, "Marked as Under Review by admin.")


@admin.action(description="Reject selected incidents")
def reject_incidents(modeladmin, request, queryset):
    for incident in queryset:
        incident.status = Incident.STATUS_REJECTED
        incident.save(update_fields=["status", "updated_at"])
        log_admin_action(request.user, AuditLog.ACTION_REJECT, incident, "Rejected by admin.")


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
    list_display = ("id", "title", "created_at", "status", "created_by")
    list_display_links = ("id", "title")
    list_editable = ("status",)
    list_filter = ("status", "category")
    search_fields = ("title", "description")
    actions = None
    actions_on_top = False
    actions_on_bottom = False

    def get_fields(self, request, obj=None):
        base_fields = ("title", "category", "description", "incident_date")
        if obj is None:
            # On create: hide status + created_by fields
            return base_fields
        # On view/edit: show status + created_by
        return base_fields + ("status", "created_by", "created_at", "updated_at", "audit_log_entries")

    def get_readonly_fields(self, request, obj=None):
        readonly = ["audit_log_entries"]
        # For system admin, keep created_by and timestamps read-only
        if obj:
            readonly.extend(["created_by", "created_at", "updated_at"])
        return readonly

    def has_add_permission(self, request):
        # Any staff can create incidents
        return request.user.is_authenticated and request.user.is_staff

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
                    log.created_at.strftime("%Y-%m-%d %H:%M"),
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
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        if not change:
            log_admin_action(request.user, AuditLog.ACTION_CREATE, obj, "Incident created by admin.")
            return

        if previous_status and previous_status != obj.status:
            if obj.status == Incident.STATUS_VERIFIED:
                action = AuditLog.ACTION_APPROVE
                message = f"Status changed from {previous_status} to {obj.status} (approved)."
            elif obj.status == Incident.STATUS_REJECTED:
                action = AuditLog.ACTION_REJECT
                message = f"Status changed from {previous_status} to {obj.status} (rejected)."
            elif obj.status == Incident.STATUS_UNDER_REVIEW:
                action = AuditLog.ACTION_UNDER_REVIEW
                message = f"Status changed from {previous_status} to {obj.status} (under review)."
            else:
                action = AuditLog.ACTION_UPDATE
                message = f"Status changed from {previous_status} to {obj.status}."
            log_admin_action(request.user, action, obj, message)
        else:
            log_admin_action(request.user, AuditLog.ACTION_UPDATE, obj, "Incident updated by admin.")
