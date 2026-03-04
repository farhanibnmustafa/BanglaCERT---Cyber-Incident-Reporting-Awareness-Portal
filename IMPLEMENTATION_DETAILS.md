# Implementation Details (Line‑By‑Line Guide)

This file explains **what I did**, **where**, and **why**.  
Each section lists the file path and a **line‑by‑line explanation** of the current code in that file.

If you change any code later, update this file to keep it accurate.

---

**Overview (What Was Implemented)**
1. Added an **Incident** model to store incident reports.
2. Added an **AuditLog** model to record admin actions (create/update/approve/reject/under review).
3. Built **admin actions and permissions** so admins can change status and logs are recorded.
4. Customized the **Django admin login page** (banner + card UI).
5. Customized admin **branding** and CSS.
6. Connected templates and static folders in `settings.py`.
7. Improved audit logs to show **status change details** with **who changed** and **when** (timestamp).

---

**File: `BanglaCERT/incidents/models.py`**
```python
from django.conf import settings               # import settings to access AUTH_USER_MODEL
from django.db import models                   # import Django ORM base classes

                                              # blank line for readability
class Incident(models.Model):                  # define the Incident database table
    STATUS_PENDING = "PENDING"                 # constant for pending status
    STATUS_UNDER_REVIEW = "UNDER_REVIEW"       # constant for under review status
    STATUS_VERIFIED = "VERIFIED"               # constant for verified status
    STATUS_REJECTED = "REJECTED"               # constant for rejected status
    STATUS_CLOSED = "CLOSED"                   # constant for closed status

    STATUS_CHOICES = [                         # list of allowed status values
        (STATUS_PENDING, "Pending"),           # pending label
        (STATUS_UNDER_REVIEW, "Under Review"), # under review label
        (STATUS_VERIFIED, "Verified"),         # verified label
        (STATUS_REJECTED, "Rejected"),         # rejected label
        (STATUS_CLOSED, "Closed"),             # closed label
    ]                                          # end status choices

    CATEGORY_CHOICES = [                       # list of incident categories
        ("phishing", "Phishing"),              # phishing label
        ("malware", "Malware"),                # malware label
        ("fraud", "Fraud"),                    # fraud label
        ("identity_theft", "Identity Theft"),  # identity theft label
        ("other", "Other"),                    # other label
    ]                                          # end category choices

    title = models.CharField(max_length=200)   # incident title
    category = models.CharField(               # incident category
        max_length=50,                         # max length for category
        choices=CATEGORY_CHOICES,              # allowed categories
        default="other"                        # default category
    )                                          # end category field
    description = models.TextField()           # incident description text
    incident_date = models.DateField()         # date when incident happened
    status = models.CharField(                 # status of the incident
        max_length=20,                         # max length for status
        choices=STATUS_CHOICES,                # allowed statuses
        default=STATUS_PENDING                 # default status is pending
    )                                          # end status field
    created_by = models.ForeignKey(            # who created the incident
        settings.AUTH_USER_MODEL,              # link to user model
        on_delete=models.SET_NULL,             # keep incident if user deleted
        null=True,                             # allow null
        blank=True,                            # allow blank in forms
        related_name="incidents_created"       # reverse relation name
    )                                          # end created_by
    created_at = models.DateTimeField(         # created time
        auto_now_add=True                      # set once on create
    )                                          # end created_at
    updated_at = models.DateTimeField(         # last updated time
        auto_now=True                          # update on every save
    )                                          # end updated_at

    def __str__(self) -> str:                  # string representation for admin
        return f"{self.title} ({self.status})" # show title + status
```

---

**File: `BanglaCERT/auditlog/models.py`**
```python
from django.conf import settings               # import settings to access AUTH_USER_MODEL
from django.db import models                   # import Django ORM base classes

                                              # blank line for readability
class AuditLog(models.Model):                  # define AuditLog database table
    ACTION_CREATE = "CREATE"                   # constant for create action
    ACTION_UPDATE = "UPDATE"                   # constant for update action
    ACTION_UNDER_REVIEW = "UNDER_REVIEW"       # constant for under review action
    ACTION_APPROVE = "APPROVE"                 # constant for approve action
    ACTION_REJECT = "REJECT"                   # constant for reject action

    ACTION_CHOICES = [                         # list of allowed action types
        (ACTION_CREATE, "Create"),             # create label
        (ACTION_UPDATE, "Update"),             # update label
        (ACTION_UNDER_REVIEW, "Under Review"), # under review label
        (ACTION_APPROVE, "Approve"),           # approve label
        (ACTION_REJECT, "Reject"),             # reject label
    ]                                          # end action choices

    user = models.ForeignKey(                  # admin user who did the action
        settings.AUTH_USER_MODEL,              # link to user model
        on_delete=models.SET_NULL,             # keep log if user deleted
        null=True,                             # allow null
        blank=True,                            # allow blank
        related_name="audit_logs"              # reverse relation name
    )                                          # end user field
    action = models.CharField(                 # action type
        max_length=20,                         # max length
        choices=ACTION_CHOICES                 # allowed actions
    )                                          # end action field
    object_type = models.CharField(max_length=100)  # model name (e.g., Incident)
    object_id = models.PositiveIntegerField()       # ID of the object
    message = models.TextField(blank=True)          # optional log message
    created_at = models.DateTimeField(auto_now_add=True)  # timestamp

    def __str__(self) -> str:                  # string representation for admin
        return f"{self.action} {self.object_type}#{self.object_id}"  # readable label
```

---

**File: `BanglaCERT/incidents/admin.py`**
```python
from django import forms                       # import Django forms for custom widget
from django.contrib import admin               # import admin site tools
from django.utils import timezone              # timezone helpers for readable timestamps
from django.utils.html import format_html, format_html_join  # safe HTML for audit log

from auditlog.models import AuditLog           # import audit log model
from .models import Incident                   # import incident model

INCIDENT_MANAGER_USERNAME = "systemadmin40329" # username allowed to delete incidents

def is_incident_manager(user):                 # helper: is this the manager user?
    return user.is_authenticated and user.username == INCIDENT_MANAGER_USERNAME

def log_admin_action(user, action, incident, message=""):  # helper to write logs
    AuditLog.objects.create(                   # create log row
        user=user,                             # who did it
        action=action,                         # what action
        object_type="Incident",                # model type
        object_id=incident.id,                 # incident id
        message=message,                       # extra detail
    )                                          # end log create

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
        incident.save(update_fields=["status", "updated_at"])
        log_status_change(request.user, incident, previous_status, incident.status)

class IncidentAdminForm(forms.ModelForm):     # custom admin form
    class Meta:                               # Django form metadata
        model = Incident                      # connect to Incident model
        fields = "__all__"                    # include all fields
        widgets = {                           # custom widgets
            "incident_date": forms.DateInput(attrs={"type": "date"}),  # HTML5 date picker
        }                                     # end widgets

@admin.register(Incident)                     # register Incident in admin
class IncidentAdmin(admin.ModelAdmin):        # admin configuration
    form = IncidentAdminForm                  # use custom form with date picker
    list_display = ("id", "title", "created_at", "status", "created_by")  # columns
    list_display_links = ("id", "title")      # clickable columns
    list_editable = ("status",)               # dropdown status in list
    list_filter = ("status", "category")      # filters on right
    search_fields = ("title", "description")  # search in list
    actions = None                            # disable bulk actions dropdown
    actions_on_top = False                    # remove action bar from top
    actions_on_bottom = False                 # remove action bar from bottom

    def get_fields(self, request, obj=None):  # choose fields for add/edit view
        base_fields = ("title", "category", "description", "incident_date")
        if obj is None:                       # create form
            return base_fields                # hide status + created_by on create
        return base_fields + ("status", "created_by", "created_at", "updated_at", "audit_log_entries")

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

    def has_change_permission(self, request, obj=None):  # who can edit
        return request.user.is_authenticated and request.user.is_staff

    def has_delete_permission(self, request, obj=None):  # who can delete
        return is_incident_manager(request.user)         # only systemadmin40329

    def has_view_permission(self, request, obj=None):    # who can view
        return request.user.is_authenticated and request.user.is_staff

    def audit_log_entries(self, obj):        # show logs inside incident detail
        if not obj:                          # no object yet
            return "-"                       # show dash
        logs = (                             # query recent logs
            AuditLog.objects.filter(object_type="Incident", object_id=obj.id)
            .order_by("-created_at")         # newest first
            .select_related("user")[:20]     # include user, limit 20
        )
        if not logs:                         # no logs found
            return "No audit log entries yet."
        items = format_html_join(            # build list items safely
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

    audit_log_entries.short_description = "Audit log"  # label in admin form

    def save_model(self, request, obj, form, change):   # save hook
        previous_status = None                          # track old status
        if change and obj.pk:                           # if editing
            previous_status = Incident.objects.filter(pk=obj.pk).values_list("status", flat=True).first()
        if not obj.created_by:                          # set creator once
            obj.created_by = request.user
        super().save_model(request, obj, form, change)  # normal save
        if not change:                                  # created new incident
            log_admin_action(
                request.user,
                AuditLog.ACTION_CREATE,
                obj,
                build_audit_message(request.user, "Incident created"),
            )
            return
        if previous_status and previous_status != obj.status:  # status changed
            log_status_change(request.user, obj, previous_status, obj.status)
        else:                                           # no status change
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
from django.contrib import admin               # import admin tools
from django.urls import reverse                # build admin link URLs
from django.utils import timezone              # format local timestamp
from django.utils.html import format_html      # safe HTML output

from incidents.models import Incident          # import Incident to show title/type
from .models import AuditLog                   # import AuditLog model

@admin.register(AuditLog)                      # register AuditLog in admin
class AuditLogAdmin(admin.ModelAdmin):         # admin configuration
    list_display = (
        "id",
        "action",
        "incident_type",
        "incident_title_link",
        "changed_by",
        "changed_at",
    )
    list_filter = ("action", "object_type")    # filter by action and object type
    search_fields = ("object_type", "object_id", "user__username", "message")
    ordering = ("-created_at",)                # newest first

    def has_add_permission(self, request):     # no one can add logs manually
        return False

    def has_change_permission(self, request, obj=None):  # no edits
        return False

    def has_delete_permission(self, request, obj=None):  # no deletes
        return False

    def has_view_permission(self, request, obj=None):    # staff can view
        return request.user.is_staff

    def incident_type(self, obj):             # show Incident category
        if obj.object_type != "Incident":
            return obj.object_type
        incident = Incident.objects.filter(id=obj.object_id).first()
        return incident.category if incident else "Incident"

    incident_type.short_description = "Incident Type"

    def incident_title_link(self, obj):       # clickable Incident title
        if obj.object_type != "Incident":
            return str(obj.object_id)
        incident = Incident.objects.filter(id=obj.object_id).first()
        if not incident:
            return "Deleted incident"
        url = reverse("admin:incidents_incident_change", args=[incident.id])
        return format_html('<a href="{}">{}</a>', url, incident.title)

    incident_title_link.short_description = "Incident Title"

    def changed_by(self, obj):                # show the admin username
        return obj.user.username if obj.user else "Unknown"

    changed_by.short_description = "Changed by"

    def changed_at(self, obj):                # formatted timestamp
        return timezone.localtime(obj.created_at).strftime("%Y-%m-%d %H:%M:%S %Z")

    changed_at.short_description = "Timestamp"
    changed_at.admin_order_field = "created_at"

```

---

**File: `BanglaCERT/templates/admin/base_site.html`**
```html
{% extends "admin/base.html" %}                  <!-- use Django admin base layout -->
{% load static %}                                <!-- enable static file usage -->

{% block title %}BanglaCERT Admin{% endblock %}   <!-- browser tab title -->

{% block branding %}                              <!-- header branding -->
<h1 id="site-name">                               <!-- admin site heading -->
    <a href="{% url 'admin:index' %}">            <!-- link to admin home -->
        <img class="admin-logo" src="{% static 'admin/img/BanglaCERT-logo.png' %}" alt="BanglaCERT logo">
        BanglaCERT Admin                           <!-- text next to logo -->
    </a>
</h1>
{% endblock %}

{% block extrastyle %}                            <!-- extra CSS -->
{{ block.super }}                                 <!-- keep default admin CSS -->
<link rel="stylesheet" href="{% static 'admin/custom_admin.css' %}">
{% endblock %}
```

---

**File: `BanglaCERT/templates/admin/login.html`**
```html
{% extends "admin/base_site.html" %}              <!-- reuse base admin layout -->
{% load i18n static %}                            <!-- i18n + static helpers -->

{% block bodyclass %}{{ block.super }} custom-admin-login{% endblock %}

{% block branding %}{% endblock %}                <!-- remove default branding -->
{% block nav-breadcrumbs %}{% endblock %}         <!-- hide breadcrumbs -->
{% block nav-sidebar %}{% endblock %}             <!-- hide sidebar -->
{% block content_title %}{% endblock %}           <!-- hide default title -->

{% block content %}
<div class="admin-login-page">                    <!-- page wrapper -->
    <div class="login-hero">                      <!-- banner area -->
        <div class="hero-inner">                  <!-- banner inner layout -->
            <div class="hero-brand">              <!-- logo/text group -->
                <div class="brand-row">           <!-- row container -->
                    <img class="brand-logo" src="{% static 'admin/img/BanglaCERT-logo.png' %}" alt="BanglaCERT logo">
                </div>
                <div class="brand-subtitle">Cyber Incident Reporting &amp; Awareness Portal</div>
            </div>
        </div>
    </div>

    <div class="login-card">                      <!-- login box -->
        <h2>Sign In to Your Account</h2>          <!-- heading -->
        <p class="login-subtitle">Sign in to manage cyber incidents.</p>

        {% if form.errors %}                      <!-- error message -->
        <p class="errornote">{% trans "Please correct the error below." %}</p>
        {% endif %}

        {% if form.non_field_errors %}            <!-- non-field errors -->
        <div class="form-error">
            {{ form.non_field_errors }}
        </div>
        {% endif %}

        <form method="post" action="{{ app_path }}" class="login-form">
            {% csrf_token %}                      <!-- CSRF protection -->
            <input type="hidden" name="next" value="{{ next }}">

            <div class="form-row">                <!-- username row -->
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
                {{ form.username.errors }}        <!-- username errors -->
            </div>

            <div class="form-row">                <!-- password row -->
                <label for="{{ form.password.id_for_label }}">Password</label>
                <input
                    type="password"
                    name="{{ form.password.html_name }}"
                    id="{{ form.password.id_for_label }}"
                    placeholder="Enter your password"
                    autocomplete="current-password"
                    required
                >
                {{ form.password.errors }}        <!-- password errors -->
            </div>

            <div class="form-row submit-row">     <!-- submit row -->
                <input type="submit" value="{% trans 'Login' %}">
            </div>

            {% if password_reset_url %}           <!-- password reset link -->
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
:root {                                         /* CSS variables */
    --brand-blue: #11436a;                      /* primary blue */
    --brand-blue-dark: #0b2d4b;                 /* dark blue */
    --brand-blue-light: #1c5d92;                /* light blue */
    --brand-gray: #eef1f6;                      /* light gray */
    --brand-card: #ffffff;                      /* card background */
    --brand-text: #1e2a35;                      /* main text color */
    --brand-muted: #6a7785;                     /* muted text color */
    --brand-green: #1f7a3a;                     /* green accent */
    --brand-red: #b32020;                       /* red accent */
}                                               /* end variables */

#header {                                       /* admin header bar */
    background: linear-gradient(90deg, var(--brand-blue-dark), var(--brand-blue));
}

#header #site-name a {                           /* header link */
    color: #ffffff;
}

.admin-logo {                                   /* header logo size */
    height: 26px;
    vertical-align: middle;
    margin-right: 8px;
}

.custom-admin-login #header,                    /* hide header on login */
.custom-admin-login nav[aria-label="Breadcrumbs"] {
    display: none;
}

.custom-admin-login #nav-sidebar,               /* hide sidebar on login */
.custom-admin-login #toggle-nav-sidebar {
    display: none;
}

#nav-sidebar #nav-filter,                       /* hide sidebar filter */
#nav-sidebar .nav-filter {
    display: none;
}

.custom-admin-login {                           /* login page background */
    background: radial-gradient(circle at top, #f6f8fb 0%, #e6ebf3 45%, #dbe2ee 100%);
    color: var(--brand-text);
}

.custom-admin-login #container {                /* full width container */
    width: 100%;
    max-width: none;
    margin: 0;
    padding: 0;
}

.custom-admin-login #content {                  /* remove extra padding */
    padding: 0;
}

.admin-login-page {                             /* full height layout */
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.login-hero {                                   /* banner section */
    background: url("img/banner.png") center/cover no-repeat;
    color: #ffffff;
    padding: 28px 40px;
    position: relative;
    overflow: hidden;
    min-height: 200px;
}

.hero-inner {                                   /* inner banner layout */
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 24px;
    max-width: 1100px;
    margin: 0 auto;
}

.hero-brand {                                   /* brand overlay */
    position: relative;
    right: 149px;
    width: 865px;
    display: inline-block;
    padding: 10px 16px;
    background: rgba(0, 0, 0, 0.1);
}

.hero-brand .brand-title {                      /* title text */
    font-size: 36px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

.brand-logo {                                   /* logo size */
    width: 70px;
    height: auto;
    margin-right: 14px;
    filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.25));
}

.brand-row {                                    /* logo row */
    display: flex;
    align-items: center;
    gap: 8px;
}

.brand-bangla {                                 /* Bangla text color */
    color: #d9f5e1;
}

.brand-cert {                                   /* CERT text color */
    color: #ffb3b3;
}

.brand-subtitle {                               /* subtitle text */
    margin-top: 6px;
    font-size: 16px;
    color: #e6eef7;
}

.hero-icons {                                   /* unused icons block */
    display: flex;
    align-items: center;
    gap: 16px;
}

.hero-icon-circle {                             /* icon circle */
    width: 72px;
    height: 72px;
    border-radius: 50%;
    border: 2px solid rgba(255, 255, 255, 0.4);
    background: rgba(255, 255, 255, 0.12);
    display: grid;
    place-items: center;
}

.hero-icon-large {                              /* larger icon circle */
    width: 96px;
    height: 96px;
}

.hero-lock {                                    /* lock icon shape */
    width: 26px;
    height: 24px;
    border: 3px solid #ffffff;
    border-radius: 4px;
    position: relative;
}

.hero-lock::before {                            /* lock top */
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

.login-card {                                   /* login card */
    max-width: 520px;
    margin: 32px auto 64px;
    padding: 30px 34px 34px;
    background: linear-gradient(180deg, #f7f8fb 0%, #ffffff 100%);
    border: 1px solid #e5e9f1;
    border-radius: 12px;
    box-shadow: 0 18px 48px rgba(17, 39, 63, 0.2);
}

.login-card h2 {                                /* card title */
    margin: 0;
    font-size: 24px;
    text-align: center;
}

.login-subtitle {                               /* card subtitle */
    text-align: center;
    color: var(--brand-muted);
    margin: 8px 0 24px;
}

.login-form .form-row {                         /* spacing between rows */
    margin-bottom: 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.login-form label {                             /* label style */
    font-weight: 600;
    display: inline-block;
    align-self: flex-start;
    padding: 3px 8px;
    border-radius: 4px;
    background: #e9ecf2;
    color: #3a4653;
}

.login-form input[type="text"],                 /* text field style */
.login-form input[type="password"] {
    height: 44px;
    border-radius: 6px;
    border: 1px solid #ccd5e1;
    padding: 0 12px;
    font-size: 15px;
    background: #f5f7fb;
    box-shadow: inset 0 1px 2px rgba(16, 24, 40, 0.06);
}

.login-form input::placeholder {                /* placeholder color */
    color: #8a95a6;
}

.login-form input[type="submit"] {              /* submit button */
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
```

---

**File: `BanglaCERT/BanglaCERT/settings.py`**
```python
TEMPLATES = [                                   # template engine settings
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],       # load templates from project-level folder
        'APP_DIRS': True,                       # also load templates from each app
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

STATIC_URL = '/static/'                          # base URL for static files
STATICFILES_DIRS = [                            # extra static file folders
    BASE_DIR / 'static',                         # project-level static
]
```

---

**Static Files Used**
1. `BanglaCERT/static/admin/img/banner.png`  
   Used as the login page banner background.
2. `BanglaCERT/static/admin/img/BanglaCERT-logo.png`  
   Used in the admin header and login banner.

---

**Admin URLs (How To Access)**
1. Admin login: `http://127.0.0.1:8000/admin/`
2. Audit logs: Admin sidebar → **Audit Logs**
3. Incidents: Admin sidebar → **Incidents**

---

**How To Verify (Admin UI)**
1. Open **Incidents** in Django admin.
2. Click any incident and change the **Status** field.
3. Save the incident.
4. In the same incident page, check **Audit log** section. You should see time, action, user, and message.
5. Open **Audit Logs** from sidebar.
6. Confirm the latest row shows **Changed by** and **Timestamp** for each log entry.

---

If you want me to update this file later (after new changes), just tell me and I will regenerate it.
