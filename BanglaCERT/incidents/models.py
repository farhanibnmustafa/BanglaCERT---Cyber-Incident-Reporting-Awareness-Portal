from django.conf import settings
from django.db import models


class Incident(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_UNDER_REVIEW = "UNDER_REVIEW"
    STATUS_VERIFIED = "VERIFIED"
    STATUS_REJECTED = "REJECTED"
    STATUS_CLOSED = "CLOSED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_UNDER_REVIEW, "Under Review"),
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
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="incidents_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.title} ({self.status})"
