# Implementation Details (Current Snapshot)

This document reflects the **current state as of March 5, 2026**.

---

<<<<<<< HEAD
**Overview (What Is Implemented Now)**
1. `Incident` model stores incident reports with status lifecycle and creator metadata.
2. `AuditLog` model stores admin actions on incidents.
3. Incident admin enforces restricted editing:
   - No admin can create incidents from Django admin.
   - On existing incidents, `title`, `description`, and `incident_date` are read-only.
   - Staff can update status.
   - Only `systemadmin40329` can delete incidents.
4. Audit log admin is read-only and shows actor/timestamp columns.
5. Admin login page, branding, and CSS are customized.
6. Templates/static directories are configured in `settings.py`.

---

**Current Admin Account State (Database Snapshot)**

From `auth_user`:

| id | username         | is_superuser | is_staff | is_active |
|---:|------------------|--------------|----------|-----------|
| 2  | systemadmin40329 | true         | true     | true      |
| 4  | IncidentChecker  | false        | true     | true      |

Operational note:
- `incidentadmin229` and `coreadmin` were fully deleted from the database.
- Related references were cleaned during deletion:
  - `django_admin_log` rows for those users were deleted.
  - `auditlog_auditlog.user_id` and `incidents_incident.created_by_id` references were set to `NULL` where applicable.
=======
**Overview (What Was Implemented)**
1. Added an **Incident** model to store incident reports.
2. Added an **AuditLog** model to record admin actions (create/update/approve/reject/under review).
3. Built **admin actions and permissions** so admins can change status and logs are recorded.
4. Customized the **Django admin login page** (banner + card UI).
5. Customized admin **branding** and CSS.
6. Connected templates and static folders in `settings.py`.
7. Improved audit logs to show **status change details** with **who changed** and **when** (timestamp).
>>>>>>> 691e920ef1f1213bcdbbe6f31796420414436752

---

**File: `BanglaCERT/incidents/models.py`**
```python
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
```

---

**File: `BanglaCERT/auditlog/models.py`**
```python
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
```

---

**File: `BanglaCERT/incidents/admin.py`**
```python
<<<<<<< HEAD
from django import forms
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html, format_html_join
=======
from django import forms                       # import Django forms for custom widget
from django.contrib import admin               # import admin site tools
from django.utils import timezone              # timezone helpers for readable timestamps
from django.utils.html import format_html, format_html_join  # safe HTML for audit log
>>>>>>> 691e920ef1f1213bcdbbe6f31796420414436752

from auditlog.models import AuditLog

from .models import Incident


INCIDENT_MANAGER_USERNAME = "systemadmin40329"


def is_incident_manager(user):
    return user.is_authenticated and user.username == INCIDENT_MANAGER_USERNAME


<<<<<<< HEAD
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


@admin.action(description="Approve selected incidents")
def approve_incidents(modeladmin, request, queryset):
    for incident in queryset:
        previous_status = incident.status
        incident.status = Incident.STATUS_VERIFIED
        incident.save(update_fields=["status", "updated_at"])
        log_status_change(request.user, incident, previous_status, incident.status)


@admin.action(description="Mark selected incidents as Under Review")
def mark_under_review(modeladmin, request, queryset):
    for incident in queryset:
        previous_status = incident.status
        incident.status = Incident.STATUS_UNDER_REVIEW
=======
def get_status_action(new_status):             # map status to audit action type
    if new_status == Incident.STATUS_VERIFIED:
        return AuditLog.ACTION_APPROVE
    if new_status == Incident.STATUS_REJECTED:
        return AuditLog.ACTION_REJECT
    if new_status == Incident.STATUS_UNDER_REVIEW:
        return AuditLog.ACTION_UNDER_REVIEW
    return AuditLog.ACTION_UPDATE

def get_status_label(status_value):            # convert DB value to human label
    return dict(Incident.STATUS_CHOICES).get(status_value, status_value)

def get_actor_context(user):                   # common actor + time details
    changed_by = user.username if user else "Unknown"
    changed_at = timezone.localtime(timezone.now()).strftime("%Y-%m-%d %H:%M:%S %Z")
    return changed_by, changed_at

def build_audit_message(user, detail):         # generic audit message with actor/time
    changed_by, changed_at = get_actor_context(user)
    return f"{detail} by {changed_by} at {changed_at}."

def build_status_change_message(user, previous_status, new_status):  # full status change message
    return build_audit_message(
        user,
        (
            f"Status changed from {get_status_label(previous_status)} "
            f"to {get_status_label(new_status)}"
        ),
    )

def log_status_change(user, incident, previous_status, new_status):  # single helper for status logs
    action = get_status_action(new_status)
    message = build_status_change_message(user, previous_status, new_status)
    log_admin_action(user, action, incident, message)

@admin.action(description="Approve selected incidents")  # admin action label
def approve_incidents(modeladmin, request, queryset):    # approve action function
    for incident in queryset:                 # loop each selected incident
        previous_status = incident.status     # keep old status for log
        incident.status = Incident.STATUS_VERIFIED  # set to verified
        incident.save(update_fields=["status", "updated_at"])  # save status only
        log_status_change(request.user, incident, previous_status, incident.status)

@admin.action(description="Mark selected incidents as Under Review")  # action label
def mark_under_review(modeladmin, request, queryset):     # under review action
    for incident in queryset:                 # loop each incident
        previous_status = incident.status     # keep old status for log
        incident.status = Incident.STATUS_UNDER_REVIEW    # set status
        incident.save(update_fields=["status", "updated_at"])
        log_status_change(request.user, incident, previous_status, incident.status)

@admin.action(description="Reject selected incidents")    # action label
def reject_incidents(modeladmin, request, queryset):      # reject action
    for incident in queryset:                 # loop each incident
        previous_status = incident.status     # keep old status for log
        incident.status = Incident.STATUS_REJECTED        # set status
>>>>>>> 691e920ef1f1213bcdbbe6f31796420414436752
        incident.save(update_fields=["status", "updated_at"])
        log_status_change(request.user, incident, previous_status, incident.status)


@admin.action(description="Reject selected incidents")
def reject_incidents(modeladmin, request, queryset):
    for incident in queryset:
        previous_status = incident.status
        incident.status = Incident.STATUS_REJECTED
        incident.save(update_fields=["status", "updated_at"])
        log_status_change(request.user, incident, previous_status, incident.status)


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

<<<<<<< HEAD
    def get_readonly_fields(self, request, obj=None):
        readonly = ["audit_log_entries"]
        # On edit, lock core incident details and metadata.
        if obj:
            readonly.extend(
                [
                    "title",
                    "description",
                    "incident_date",
                    "created_by",
                    "created_at",
                    "updated_at",
                ]
            )
        return readonly

    def has_add_permission(self, request):
        # Incident creation is disabled in admin for all users.
        return False

    def has_change_permission(self, request, obj=None):
        # Any staff can change incidents (including incidentadmin229)
        return request.user.is_authenticated and request.user.is_staff
=======
    def get_readonly_fields(self, request, obj=None):  # fields that cannot be edited
        readonly = ["audit_log_entries"]      # audit log is read‑only
        if obj:                               # if editing existing incident
            readonly.extend([                 # lock core incident details + metadata
                "title",
                "description",
                "incident_date",
                "created_by",
                "created_at",
                "updated_at",
            ])
        return readonly

    def has_add_permission(self, request):    # creation is disabled in admin
        return False                           # no admin can create incidents
>>>>>>> 691e920ef1f1213bcdbbe6f31796420414436752

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
        if not obj.created_by:
            obj.created_by = request.user
<<<<<<< HEAD
        super().save_model(request, obj, form, change)
        if not change:
=======
        super().save_model(request, obj, form, change)  # normal save
        if not change:                                  # created new incident
>>>>>>> 691e920ef1f1213bcdbbe6f31796420414436752
            log_admin_action(
                request.user,
                AuditLog.ACTION_CREATE,
                obj,
                build_audit_message(request.user, "Incident created"),
            )
            return
<<<<<<< HEAD

        if previous_status and previous_status != obj.status:
            log_status_change(request.user, obj, previous_status, obj.status)
        else:
=======
        if previous_status and previous_status != obj.status:  # status changed
            log_status_change(request.user, obj, previous_status, obj.status)
        else:                                           # no status change
>>>>>>> 691e920ef1f1213bcdbbe6f31796420414436752
            log_admin_action(
                request.user,
                AuditLog.ACTION_UPDATE,
                obj,
                build_audit_message(request.user, "Incident updated"),
            )
```

---

**File: `BanglaCERT/auditlog/admin.py`**
```python
<<<<<<< HEAD
from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
=======
from django.contrib import admin               # import admin tools
from django.urls import reverse                # build admin link URLs
from django.utils import timezone              # format local timestamp
from django.utils.html import format_html      # safe HTML output
>>>>>>> 691e920ef1f1213bcdbbe6f31796420414436752

from incidents.models import Incident

<<<<<<< HEAD
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
=======
@admin.register(AuditLog)                      # register AuditLog in admin
class AuditLogAdmin(admin.ModelAdmin):         # admin configuration
>>>>>>> 691e920ef1f1213bcdbbe6f31796420414436752
    list_display = (
        "id",
        "action",
        "incident_type",
        "incident_title_link",
        "changed_by",
        "changed_at",
    )
<<<<<<< HEAD
    list_filter = ("action", "object_type")
=======
    list_filter = ("action", "object_type")    # filter by action and object type
>>>>>>> 691e920ef1f1213bcdbbe6f31796420414436752
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

<<<<<<< HEAD
    def changed_at(self, obj):
=======
    def changed_at(self, obj):                # formatted timestamp
>>>>>>> 691e920ef1f1213bcdbbe6f31796420414436752
        return timezone.localtime(obj.created_at).strftime("%Y-%m-%d %H:%M:%S %Z")

    changed_at.short_description = "Timestamp"
    changed_at.admin_order_field = "created_at"
<<<<<<< HEAD
=======

>>>>>>> 691e920ef1f1213bcdbbe6f31796420414436752
```

---

**File: `BanglaCERT/templates/admin/base_site.html`**
```html
{% extends "admin/base.html" %}
{% load static %}

{% block title %}BanglaCERT Admin{% endblock %}

{% block branding %}
<h1 id="site-name">
    <a href="{% url 'admin:index' %}">
        <img class="admin-logo" src="{% static 'admin/img/BanglaCERT-logo.png' %}" alt="BanglaCERT logo">
        BanglaCERT Admin
    </a>
</h1>
{% endblock %}

{% block extrastyle %}
{{ block.super }}
<link rel="stylesheet" href="{% static 'admin/custom_admin.css' %}?v=20260223">
{% endblock %}
```

---

**File: `BanglaCERT/templates/admin/login.html`**
```html
{% extends "admin/base_site.html" %}
{% load i18n static %}

{% block bodyclass %}{{ block.super }} custom-admin-login{% endblock %}

{% block branding %}{% endblock %}

{% block nav-breadcrumbs %}{% endblock %}

{% block nav-sidebar %}{% endblock %}

{% block content_title %}{% endblock %}

{% block content %}
<div class="admin-login-page">
    <div class="login-hero">
        <div class="hero-inner">
            <div class="hero-brand">
                <div class="brand-row">
                    <img class="brand-logo" src="{% static 'admin/img/BanglaCERT-logo.png' %}" alt="BanglaCERT logo">
                </div>
                <div class="brand-subtitle">Cyber Incident Reporting &amp; Awareness Portal</div>
            </div>
        </div>
    </div>

    <div class="login-card">
        <h2>Sign In to Your Account</h2>
        <p class="login-subtitle">Sign in to manage cyber incidents.</p>

        {% if form.errors %}
        <p class="errornote">{% trans "Please correct the error below." %}</p>
        {% endif %}

        {% if form.non_field_errors %}
        <div class="form-error">
            {{ form.non_field_errors }}
        </div>
        {% endif %}

        <form method="post" action="{{ app_path }}" class="login-form">
            {% csrf_token %}
            <input type="hidden" name="next" value="{{ next }}">

            <div class="form-row">
                <label for="{{ form.username.id_for_label }}">UserID</label>
                <input
                    type="text"
                    name="{{ form.username.html_name }}"
                    id="{{ form.username.id_for_label }}"
                    value="{{ form.username.value|default_if_none:'' }}"
                    placeholder="Enter your admin userID"
                    autocomplete="username"
                    required
                >
                {{ form.username.errors }}
            </div>

            <div class="form-row">
                <label for="{{ form.password.id_for_label }}">Password</label>
                <input
                    type="password"
                    name="{{ form.password.html_name }}"
                    id="{{ form.password.id_for_label }}"
                    placeholder="Enter your password"
                    autocomplete="current-password"
                    required
                >
                {{ form.password.errors }}
            </div>

            <div class="form-row submit-row">
                <input type="submit" value="{% trans 'Login' %}">
            </div>

            {% if password_reset_url %}
            <div class="password-reset-link">
                <a href="{{ password_reset_url }}">{% trans "Forgotten your password or username?" %}</a>
            </div>
            {% endif %}
        </form>
    </div>
</div>
{% endblock %}
```

---

**File: `BanglaCERT/static/admin/custom_admin.css`**
```css
:root {
    --brand-blue: #11436a;
    --brand-blue-dark: #0b2d4b;
    --brand-blue-light: #1c5d92;
    --brand-gray: #eef1f6;
    --brand-card: #ffffff;
    --brand-text: #1e2a35;
    --brand-muted: #6a7785;
    --brand-green: #1f7a3a;
    --brand-red: #b32020;
}

/* Admin header (kept subtle for non-login pages) */
#header {
    background: linear-gradient(90deg, var(--brand-blue-dark), var(--brand-blue));
}

#header #site-name a {
    color: #ffffff;
}

.admin-logo {
    height: 26px;
    vertical-align: middle;
    margin-right: 8px;
}

/* Hide header + breadcrumbs on login page */
.custom-admin-login #header,
.custom-admin-login nav[aria-label="Breadcrumbs"] {
    display: none;
}

/* Hide admin sidebar + toggle on login page */
.custom-admin-login #nav-sidebar,
.custom-admin-login #toggle-nav-sidebar {
    display: none;
}

/* Hide admin sidebar filter (search box) */
#nav-sidebar #nav-filter,
#nav-sidebar .nav-filter {
    display: none;
}

/* Login page layout */
.custom-admin-login {
    background: radial-gradient(circle at top, #f6f8fb 0%, #e6ebf3 45%, #dbe2ee 100%);
    color: var(--brand-text);
}

.custom-admin-login #container {
    width: 100%;
    max-width: none;
    margin: 0;
    padding: 0;
}

.custom-admin-login #content {
    padding: 0;
}

.admin-login-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.login-hero {
    background: url("img/banner.png") center/cover no-repeat;
    color: #ffffff;
    padding: 28px 40px;
    position: relative;
    overflow: hidden;
    min-height: 200px;
}

.hero-inner {
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 24px;
    max-width: 1100px;
    margin: 0 auto;
}

.hero-brand {
    position: relative;
    right: 149px;
    width: 865px;
    display: inline-block;
    padding: 10px 16px;
    /* border-radius: 8px; */
    background: rgba(0, 0, 0, 0.1);
}

.hero-brand .brand-title {
    font-size: 36px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

.brand-logo {
    width: 275px;
    height: auto;
    margin-left: 19px;
    margin-right: 0;
    filter: drop-shadow(0 4px 12px rgba(255, 255, 255, 0.95));
}

.brand-row {
    display: flex;
    align-items: center;
    gap: 8px;
}

.brand-bangla {
    color: #d9f5e1;
}

.brand-cert {
    color: #ffb3b3;
}

.brand-subtitle {
    margin-top: -85px;
    margin-left: 140px;
    font-size: 12px;
    line-height: 1.25;
    font-weight: 600;
    color: #e6eef7;
    text-shadow: 0 2px 8px rgba(0, 0, 0, 0.45);
    max-width: 430px;
}

.hero-icons {
    display: flex;
    align-items: center;
    gap: 16px;
}

.hero-icon-circle {
    width: 72px;
    height: 72px;
    border-radius: 50%;
    border: 2px solid rgba(255, 255, 255, 0.4);
    background: rgba(255, 255, 255, 0.12);
    display: grid;
    place-items: center;
}

.hero-icon-large {
    width: 96px;
    height: 96px;
}

.hero-lock {
    width: 26px;
    height: 24px;
    border: 3px solid #ffffff;
    border-radius: 4px;
    position: relative;
}

.hero-lock::before {
    content: "";
    position: absolute;
    width: 18px;
    height: 16px;
    border: 3px solid #ffffff;
    border-bottom: none;
    border-radius: 12px 12px 0 0;
    left: 50%;
    transform: translateX(-50%);
    top: -18px;
    background: transparent;
}

.login-card {
    max-width: 520px;
    margin: 32px auto 64px;
    padding: 30px 34px 34px;
    background: linear-gradient(180deg, #f7f8fb 0%, #ffffff 100%);
    border: 1px solid #e5e9f1;
    border-radius: 12px;
    box-shadow: 0 18px 48px rgba(17, 39, 63, 0.2);
}

.login-card h2 {
    margin: 0;
    font-size: 24px;
    text-align: center;
}

.login-subtitle {
    text-align: center;
    color: var(--brand-muted);
    margin: 8px 0 24px;
}

.login-form .form-row {
    margin-bottom: 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.login-form label {
    font-weight: 600;
    display: inline-block;
    align-self: flex-start;
    padding: 3px 8px;
    border-radius: 4px;
    background: #e9ecf2;
    color: #3a4653;
}

.login-form input[type="text"],
.login-form input[type="password"] {
    height: 44px;
    border-radius: 6px;
    border: 1px solid #ccd5e1;
    padding: 0 12px;
    font-size: 15px;
    background: #f5f7fb;
    box-shadow: inset 0 1px 2px rgba(16, 24, 40, 0.06);
}

.login-form input::placeholder {
    color: #8a95a6;
}

.login-form input[type="submit"] {
    width: 100%;
    height: 44px;
    border: none;
    border-radius: 6px;
    background: linear-gradient(90deg, #1d5fa8, #0c3d7a);
    color: #ffffff;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
}

.login-form input[type="submit"]:hover {
    opacity: 0.95;
}

.errornote,
.form-error {
    background: #fff2f2;
    border: 1px solid #f1bcbc;
    color: #9b1b1b;
    padding: 10px 12px;
    border-radius: 6px;
    margin-bottom: 16px;
}

.password-reset-link {
    margin-top: 14px;
    text-align: center;
}

.password-reset-link a {
    color: var(--brand-blue);
}

@media (max-width: 768px) {
    .hero-inner {
        flex-direction: column;
        align-items: flex-start;
    }

    .brand-logo {
        width: 215px;
        margin-left: 0;
    }

    .brand-subtitle {
        margin-top: 8px;
        margin-left: 0;
        font-size: 14px;
        max-width: none;
    }

    .hero-icons {
        display: none;
    }

    .login-card {
        margin: 24px 16px 48px;
        padding: 24px;
    }
}
```

---

**File: `BanglaCERT/BanglaCERT/settings.py` (relevant sections)**
```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
<<<<<<< HEAD
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
=======

STATIC_URL = '/static/'                          # base URL for static files
STATICFILES_DIRS = [                            # extra static file folders
    BASE_DIR / 'static',                         # project-level static
>>>>>>> 691e920ef1f1213bcdbbe6f31796420414436752
]
```

---

**Static Files Used**
1. `BanglaCERT/static/admin/img/banner.png`  
   Used as the login-page banner background.
2. `BanglaCERT/static/admin/img/BanglaCERT-logo.png`  
   Used in admin header and login page.

---

**Admin URLs**
1. Admin login: `http://127.0.0.1:8000/admin/`
2. Audit logs: Admin sidebar -> **Audit Logs**
3. Incidents: Admin sidebar -> **Incidents**

---

**How To Verify (Admin UI)**
<<<<<<< HEAD
1. Login as `systemadmin40329`.
2. Open **Incidents**.
3. Confirm there is no **Add Incident** button.
4. Open an existing incident:
   - `title`, `description`, and `incident_date` should be read-only.
   - `status` should be editable.
5. Change `status` and save.
6. Check incident's **Audit log** field: entries should include action, user, timestamp, and message text.
7. Open **Audit Logs**:
   - List shows `Changed by` and `Timestamp` columns.
   - There is no `Status Update Details` column.

---


=======
1. Open **Incidents** in Django admin.
2. Click any incident and change the **Status** field.
3. Save the incident.
4. In the same incident page, check **Audit log** section. You should see time, action, user, and message.
5. Open **Audit Logs** from sidebar.
6. Confirm the latest row shows **Changed by** and **Timestamp** for each log entry.

---

If you want me to update this file later (after new changes), just tell me and I will regenerate it.
>>>>>>> 691e920ef1f1213bcdbbe6f31796420414436752
