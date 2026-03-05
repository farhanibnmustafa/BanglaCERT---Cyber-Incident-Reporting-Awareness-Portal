from django.conf import settings
from django.db import models


class Incident(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_UNDER_REVIEW = "UNDER_REVIEW"
    STATUS_NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    STATUS_VERIFIED = "VERIFIED"
    STATUS_REJECTED = "REJECTED"
    STATUS_CLOSED = "CLOSED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_UNDER_REVIEW, "Under Review"),
        (STATUS_NEEDS_CLARIFICATION, "Needs Clarification"),
        (STATUS_VERIFIED, "Verified"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_CLOSED, "Closed"),
    ]

    CATEGORY_CHOICES = [
        ("phishing", "Phishing"),
        ("malware", "Malware"),
        ("fraud", "Fraud"),
        ("identity_theft", "Identity Theft"),
        ("other", "Other"),
    ]

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="other")
    description = models.TextField()
    incident_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    is_anonymous = models.BooleanField(default=False)
    reporter_email = models.EmailField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="incidents_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.title} ({self.status})"

    @property
    def reporter_display_name(self) -> str:
        if self.is_anonymous or not self.created_by:
            return "Anonymous"
        return self.created_by.username


class IncidentComment(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="comments")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="incident_comments"
    )
    comment = models.TextField()
    is_admin_note = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self) -> str:
        author = self.created_by.username if self.created_by else "Unknown"
        return f"Comment by {author} on Incident#{self.incident_id}"
