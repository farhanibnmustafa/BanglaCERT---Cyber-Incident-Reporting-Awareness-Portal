from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import redirect_to_login
from django.db.models import Count, Q
from django.http import HttpResponseNotAllowed, JsonResponse
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.forms import StaffPromotionForm, StaffUserCreationForm, UserRegistrationForm, ManageStaffUserForm
from analytics.services import build_analytics_dashboard
from auditlog.models import AuditLog

from incidents.forms import IncidentStaffCategoryForm, IncidentStaffCommentForm, IncidentStaffFilterForm, IncidentStaffStatusForm
from incidents.models import Incident
from incidents.staff_tools import (
    build_audit_message,
    can_manage_staff_users,
    has_staff_users,
    log_staff_action,
    log_status_change,
    notify_status_change,
)
from notifications.services import resend_incident_notification


User = get_user_model()


def staff_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not has_staff_users():
            return redirect("admin:setup")
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), login_url=reverse("accounts:staff_login"))
        if not request.user.is_staff:
            messages.error(request, "You do not have access to the incident admin dashboard.")
            return redirect("incidents:my_incidents")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def manager_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not has_staff_users():
            return redirect("admin:setup")
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), login_url=reverse("accounts:staff_login"))
        if not can_manage_staff_users(request.user):
            messages.error(request, "Only the main admin can manage staff accounts.")
            return redirect("admin:index")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def _admin_context(request):
    return {
        "can_manage_staff_users": can_manage_staff_users(request.user),
    }


def _status_summary():
    counts = {
        row["status"]: row["total"]
        for row in Incident.objects.values("status").annotate(total=Count("id"))
    }
    return [
        {
            "value": status_value,
            "label": status_label,
            "count": counts.get(status_value, 0),
        }
        for status_value, status_label in Incident.STATUS_CHOICES
    ]


def _build_dashboard_queryset(form):
    incidents = Incident.objects.select_related("created_by").order_by("-updated_at", "-created_at")
    if not form.is_valid():
        return incidents

    query = form.cleaned_data.get("q", "").strip()
    status = form.cleaned_data.get("status")
    category = form.cleaned_data.get("category")

    if query:
        incidents = incidents.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(reporter_email__icontains=query)
            | Q(created_by__username__icontains=query)
        )
    if status:
        incidents = incidents.filter(status=status)
    if category:
        incidents = incidents.filter(category=category)
    return incidents


def _get_staff_incident(incident_id):
    return get_object_or_404(Incident.objects.select_related("created_by"), id=incident_id)


def _get_audit_logs(incident):
    return (
        AuditLog.objects.filter(object_type="Incident", object_id=incident.id)
        .select_related("user")
        .order_by("-created_at")[:20]
    )


def _category_label(category_value):
    return dict(Incident.CATEGORY_CHOICES).get(category_value, category_value)


@staff_required
def dashboard(request):
    filter_form = IncidentStaffFilterForm(request.GET or None)
    incidents = _build_dashboard_queryset(filter_form)
    context = {
        **_admin_context(request),
        "incidents": incidents,
        "filter_form": filter_form,
        "status_summary": _status_summary(),
        **build_analytics_dashboard(scope="all"),
    }
    return render(request, "incidents/admin_dashboard.html", context)


@staff_required
def incident_detail(request, incident_id):
    incident = _get_staff_incident(incident_id)
    comments = incident.comments.select_related("created_by").all()
    context = {
        **_admin_context(request),
        "incident": incident,
        "comments": comments,
        "evidence_files": incident.evidence_files.all(),
        "audit_logs": _get_audit_logs(incident),
        "category_form": IncidentStaffCategoryForm(instance=incident),
        "status_form": IncidentStaffStatusForm(instance=incident),
        "comment_form": IncidentStaffCommentForm(),
    }
    return render(request, "incidents/admin_incident_detail.html", context)


def setup_first_admin(request):
    if has_staff_users():
        if request.user.is_authenticated and request.user.is_staff:
            return redirect("admin:index")
        messages.info(request, "An admin account already exists. Please sign in.")
        return redirect("accounts:staff_login")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            login(request, user)
            messages.success(request, "First admin account created successfully.")
            return redirect("admin:index")
    else:
        form = UserRegistrationForm()

    return render(
        request,
        "incidents/admin_setup.html",
        {
            "form": form,
        },
    )


@manager_required
def staff_accounts(request):
    create_form = StaffUserCreationForm(prefix="create")
    promote_form = StaffPromotionForm(prefix="promote")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "create_staff":
            create_form = StaffUserCreationForm(request.POST, prefix="create")
            if create_form.is_valid():
                user = create_form.save()
                messages.success(request, f"Staff account created for {user.email}.")
                return redirect("admin:staff_accounts")
        elif action == "promote_staff":
            promote_form = StaffPromotionForm(request.POST, prefix="promote")
            if promote_form.is_valid():
                user = promote_form.cleaned_data["user"]
                user.is_staff = True
                user.is_superuser = False
                user.save(update_fields=["is_staff", "is_superuser"])
                messages.success(request, f"{user.username} is now a staff user.")
                return redirect("admin:staff_accounts")
        else:
            messages.error(request, "Unknown staff action.")

    staff_users = User.objects.filter(is_staff=True).order_by("-is_superuser", "username")
    normal_users = User.objects.filter(is_staff=False).order_by("username")
    context = {
        **_admin_context(request),
        "create_form": create_form,
        "promote_form": promote_form,
        "staff_users": staff_users,
        "normal_users": normal_users,
    }
    return render(request, "incidents/admin_staff_accounts.html", context)


@staff_required
def update_incident_category(request, incident_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    incident = _get_staff_incident(incident_id)
    previous_category = incident.category
    form = IncidentStaffCategoryForm(request.POST, instance=incident)
    if not form.is_valid():
        messages.error(request, "Could not update the incident category.")
        return redirect("admin:incident_detail", incident_id=incident.id)

    updated_incident = form.save(commit=False)
    new_category = updated_incident.category
    if previous_category == new_category:
        messages.info(request, "The incident category was not changed.")
        return redirect("admin:incident_detail", incident_id=incident.id)

    incident.category = new_category
    incident.save(update_fields=["category", "updated_at"])
    log_staff_action(
        request.user,
        AuditLog.ACTION_UPDATE,
        incident,
        build_audit_message(
            request.user,
            f"Category changed from {_category_label(previous_category)} to {_category_label(new_category)}",
        ),
    )
    messages.success(request, "Incident category updated.")
    return redirect("admin:incident_detail", incident_id=incident.id)


@staff_required
def update_incident_status(request, incident_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    incident = _get_staff_incident(incident_id)
    previous_status = incident.status
    form = IncidentStaffStatusForm(request.POST, instance=incident)
    if not form.is_valid():
        messages.error(request, "Could not update the incident status.")
        return redirect("admin:incident_detail", incident_id=incident.id)

    updated_incident = form.save(commit=False)
    new_status = updated_incident.status
    if previous_status == new_status:
        messages.info(request, "The incident status was not changed.")
        return redirect("admin:incident_detail", incident_id=incident.id)

    incident.status = new_status
    incident.save(update_fields=["status", "updated_at"])
    log_status_change(request.user, incident, previous_status, incident.status)

    sent, reason = notify_status_change(incident, previous_status, incident.status)
    if sent:
        messages.success(request, "Incident status updated.")
    else:
        messages.warning(request, f"Incident status updated, but the notification email was not sent: {reason}")

    return redirect("admin:incident_detail", incident_id=incident.id)


@staff_required
def add_incident_comment(request, incident_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    incident = _get_staff_incident(incident_id)
    form = IncidentStaffCommentForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Could not save the admin note.")
        return redirect("admin:incident_detail", incident_id=incident.id)

    comment = form.save(commit=False)
    comment.incident = incident
    comment.created_by = request.user
    comment.is_admin_note = True
    comment.save()

    log_staff_action(
        request.user,
        AuditLog.ACTION_UPDATE,
        incident,
        build_audit_message(request.user, "Admin note added"),
    )
    messages.success(request, "Admin note added.")
    return redirect("admin:incident_detail", incident_id=incident.id)


@staff_required
def inline_update_incident(request, incident_id):
    """JSON endpoint for quick status/category updates from the dashboard table."""
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    import json
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    field = payload.get("field")  # "status" or "category"
    value = payload.get("value", "").strip()

    if field not in ("status", "category") or not value:
        return JsonResponse({"error": "Invalid field or value"}, status=400)

    incident = get_object_or_404(Incident, id=incident_id)

    if field == "status":
        valid_values = dict(Incident.STATUS_CHOICES)
        if value not in valid_values:
            return JsonResponse({"error": "Invalid status value"}, status=400)
        previous = incident.status
        if previous == value:
            return JsonResponse({"ok": True, "display": incident.get_status_display(), "unchanged": True})
        incident.status = value
        incident.save(update_fields=["status", "updated_at"])
        log_status_change(request.user, incident, previous, value)
        notify_status_change(incident, previous, value)
        return JsonResponse({"ok": True, "display": incident.get_status_display()})

    elif field == "category":
        valid_values = dict(Incident.CATEGORY_CHOICES)
        if value not in valid_values:
            return JsonResponse({"error": "Invalid category value"}, status=400)
        previous = incident.category
        if previous == value:
            return JsonResponse({"ok": True, "display": incident.get_category_display(), "unchanged": True})
        incident.category = value
        incident.save(update_fields=["category", "updated_at"])
        log_staff_action(
            request.user,
            AuditLog.ACTION_UPDATE,
            incident,
            build_audit_message(
                request.user,
                f"Category changed from {_category_label(previous)} to {_category_label(value)}",
            ),
        )
        return JsonResponse({"ok": True, "display": incident.get_category_display()})


@staff_required
def resend_incident_email(request, incident_id):
    """Resend a submission or status notification email to the reporter."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    incident = get_object_or_404(Incident, id=incident_id)
    notification_type = request.POST.get("notification_type", "").strip()

    if notification_type not in ("submission", "status"):
        messages.error(request, "Invalid notification type.")
        return redirect("admin:incident_detail", incident_id=incident.id)

    recipient = incident.reporter_email or (
        incident.created_by.email if incident.created_by else ""
    )
    if not recipient:
        messages.error(request, "No email address available for this reporter.")
        return redirect("admin:incident_detail", incident_id=incident.id)

    sent, reason = resend_incident_notification(incident, notification_type)

    if sent:
        log_staff_action(
            request.user,
            AuditLog.ACTION_UPDATE,
            incident,
            build_audit_message(
                request.user, f"Resent {notification_type} email to {recipient}"
            ),
        )
        messages.success(request, f"Email notification ({notification_type}) resent to {recipient}.")
    else:
        messages.error(request, f"Failed to send email notification: {reason}")

    return redirect("admin:incident_detail", incident_id=incident.id)


@manager_required
def toggle_staff_active(request, user_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    target_user = get_object_or_404(User, id=user_id, is_staff=True)

    if target_user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect("admin:staff_accounts")

    target_user.is_active = not target_user.is_active
    target_user.save(update_fields=["is_active"])

    status = "activated" if target_user.is_active else "deactivated"
    messages.success(request, f"Account for {target_user.username} has been {status}.")
    return redirect("admin:staff_accounts")


@manager_required
def remove_staff_access(request, user_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    target_user = get_object_or_404(User, id=user_id, is_staff=True)

    if target_user == request.user:
        messages.error(request, "You cannot remove your own staff access.")
        return redirect("admin:staff_accounts")

    target_user.is_staff = False
    target_user.save(update_fields=["is_staff"])

    messages.success(request, f"Staff access revoked for {target_user.username}. They are now a normal user.")
    return redirect("admin:staff_accounts")


@manager_required
def edit_staff_user(request, user_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    target_user = get_object_or_404(User, id=user_id, is_staff=True)
    form = ManageStaffUserForm(request.POST, instance=target_user)

    if form.is_valid():
        # Prevent self-deactivation via form as well
        if target_user == request.user and not form.cleaned_data.get("is_active"):
            messages.error(request, "You cannot deactivate your own account.")
            return redirect("admin:staff_accounts")

        form.save()
        messages.success(request, f"Account details for {target_user.username} updated.")
    else:
        error_msg = " ".join([" ".join(errors) for errors in form.errors.values()])
        messages.error(request, f"Could not update staff account: {error_msg}")

    return redirect("admin:staff_accounts")
