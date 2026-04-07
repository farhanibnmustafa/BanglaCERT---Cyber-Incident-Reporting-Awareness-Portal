from django.conf import settings
from django.db import models

from incidents.models import Incident


class AwarenessComment(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="awareness_comments")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="awareness_comments",
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self) -> str:
        author = self.created_by.username if self.created_by else "Unknown"
        return f"Awareness comment by {author} on Incident#{self.incident_id}"


class AwarenessLike(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="awareness_likes")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="awareness_likes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("incident", "created_by"), name="unique_awareness_like_per_user"),
        ]
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.created_by.username} liked Incident#{self.incident_id}"


class AwarenessShare(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="awareness_shares")
    shared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="awareness_shares",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        actor = self.shared_by.username if self.shared_by else "Anonymous"
        return f"{actor} shared Incident#{self.incident_id}"
