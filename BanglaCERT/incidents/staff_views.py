from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import redirect_to_login
from django.db.models import Count, Q
from django.http import HttpResponseNotAllowed
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from accounts.forms import StaffPromotionForm, StaffUserCreationForm, UserRegistrationForm
from auditlog.models import AuditLog

from .forms import IncidentStaffCommentForm, IncidentStaffFilterForm, IncidentStaffStatusForm
from .models import Incident
from .staff_tools import (
    build_audit_message,
    can_manage_staff_users,
    has_staff_users,
    log_staff_action,
    log_status_change,
    notify_status_change,
)


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


@staff_required
def dashboard(request):
    filter_form = IncidentStaffFilterForm(request.GET or None)
    incidents = _build_dashboard_queryset(filter_form)
    context = {
        **_admin_context(request),
        "incidents": incidents,
        "filter_form": filter_form,
        "status_summary": _status_summary(),
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
        "audit_logs": _get_audit_logs(incident),
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
