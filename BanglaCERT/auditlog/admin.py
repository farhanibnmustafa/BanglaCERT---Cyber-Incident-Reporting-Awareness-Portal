from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from incidents.models import Incident

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "action",
        "incident_type",
        "incident_title_link",
        "changed_by",
        "changed_at",
    )
    list_filter = ("action", "object_type")
    search_fields = ("object_type", "object_id", "user__username", "message")
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff

    def incident_type(self, obj):
        if obj.object_type != "Incident":
            return obj.object_type
        incident = Incident.objects.filter(id=obj.object_id).first()
        return incident.category if incident else "Incident"

    incident_type.short_description = "Incident Type"

    def incident_title_link(self, obj):
        if obj.object_type != "Incident":
            return str(obj.object_id)
        incident = Incident.objects.filter(id=obj.object_id).first()
        if not incident:
            return "Deleted incident"
        url = reverse("admin:incidents_incident_change", args=[incident.id])
        return format_html('<a href="{}">{}</a>', url, incident.title)

    incident_title_link.short_description = "Incident Title"

    def changed_by(self, obj):
        return obj.user.username if obj.user else "Unknown"

    changed_by.short_description = "Changed by"

    def changed_at(self, obj):
        return timezone.localtime(obj.created_at).strftime("%Y-%m-%d %H:%M:%S %Z")

    changed_at.short_description = "Timestamp"
    changed_at.admin_order_field = "created_at"
