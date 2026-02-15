from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    ACTION_CREATE = "CREATE"
    ACTION_UPDATE = "UPDATE"
    ACTION_UNDER_REVIEW = "UNDER_REVIEW"
    ACTION_APPROVE = "APPROVE"
    ACTION_REJECT = "REJECT"

    ACTION_CHOICES = [
        (ACTION_CREATE, "Create"),
        (ACTION_UPDATE, "Update"),
        (ACTION_UNDER_REVIEW, "Under Review"),
        (ACTION_APPROVE, "Approve"),
        (ACTION_REJECT, "Reject"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs"
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    object_type = models.CharField(max_length=100)
    object_id = models.PositiveIntegerField()
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.action} {self.object_type}#{self.object_id}"
