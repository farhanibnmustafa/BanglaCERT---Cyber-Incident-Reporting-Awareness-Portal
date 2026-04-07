import secrets
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


ALLOWED_EVIDENCE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf"}
MAX_EVIDENCE_FILE_SIZE = 5 * 1024 * 1024


def validate_evidence_file(uploaded_file):
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix not in ALLOWED_EVIDENCE_EXTENSIONS:
        raise ValidationError("Allowed evidence formats: PNG, JPG, JPEG, PDF.")
    if uploaded_file.size > MAX_EVIDENCE_FILE_SIZE:
        raise ValidationError("Each evidence file must be 5 MB or smaller.")


def incident_evidence_upload_to(instance, filename):
    suffix = Path(filename).suffix.lower()
    incident_id = instance.incident_id or "unassigned"
    return f"incident_evidence/{incident_id}/{uuid4().hex}{suffix}"


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
    is_anonymous = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reporter_email = models.EmailField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="incidents_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    public_tracking_id = models.CharField(max_length=32, unique=True, null=True, blank=True, db_index=True)
    public_tracking_token = models.CharField(max_length=64, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.title} ({self.status})"

    @property
    def reporter_display_name(self) -> str:
        if self.is_anonymous or not self.created_by:
            return "Anonymous"
        return self.created_by.username

    def ensure_public_tracking_credentials(self):
        updated_fields = []
        if not self.public_tracking_id:
            if not self.pk:
                raise ValueError("Tracking credentials require a saved incident.")
            self.public_tracking_id = f"BC-{self.pk:06d}-{secrets.token_hex(2).upper()}"
            updated_fields.append("public_tracking_id")
        if not self.public_tracking_token:
            self.public_tracking_token = secrets.token_hex(16)
            updated_fields.append("public_tracking_token")
        return updated_fields


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


class IncidentEvidence(models.Model):
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE, related_name="evidence_files")
    file = models.FileField(upload_to=incident_evidence_upload_to, validators=[validate_evidence_file])
    original_name = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="incident_evidence"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        if self.file and not self.original_name:
            self.original_name = Path(self.file.name).name
        super().save(*args, **kwargs)

    @property
    def display_name(self) -> str:
        return self.original_name or Path(self.file.name).name

    def __str__(self) -> str:
        return f"Evidence for Incident#{self.incident_id}: {self.display_name}"
