from django.db import models
from django.conf import settings
from incidents.models import Incident

class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,  # Null for anonymous incident-based tracking
        blank=True
    )
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='system_notifications'
    )
    message = models.TextField()
    url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient or 'Incident #' + str(self.incident.id)}: {self.message[:30]}"
