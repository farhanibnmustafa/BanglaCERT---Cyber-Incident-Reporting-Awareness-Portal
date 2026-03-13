from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from .forms import IncidentCommentForm, IncidentReportForm
from .models import Incident


def get_incident_for_user(user, incident_id):
    return get_object_or_404(Incident, id=incident_id, created_by=user)


def home(request):
    if not request.user.is_authenticated:
        return redirect("incidents:report")
    if request.user.is_staff:
        return redirect("admin:index")
    return redirect("incidents:my_incidents")


def report_incident(request):
    if request.user.is_authenticated and request.user.is_staff:
        messages.info(request, "Staff users should manage incidents from Django admin.")
        return redirect("admin:index")

    if request.method == "POST":
        form = IncidentReportForm(
            request.POST,
            require_reporter_email=not request.user.is_authenticated,
            anonymous_default=not request.user.is_authenticated,
        )
        if form.is_valid():
            incident = form.save(commit=False)
            if request.user.is_authenticated and request.user.email and not incident.reporter_email:
                incident.reporter_email = request.user.email
            if request.user.is_authenticated and not incident.is_anonymous:
                incident.created_by = request.user
            else:
                incident.created_by = None
                incident.is_anonymous = True
            incident.save()
            messages.success(request, "Incident submitted successfully.")
            if incident.created_by:
                return redirect("incidents:detail", incident_id=incident.id)
            return redirect("incidents:report_success")
    else:
        form = IncidentReportForm(
            require_reporter_email=not request.user.is_authenticated,
            anonymous_default=not request.user.is_authenticated,
        )
    return render(request, "incidents/report_incident.html", {"form": form})


def public_report_success(request):
    return render(request, "incidents/report_success.html")


@login_required
def my_incidents(request):
    if request.user.is_staff:
        return redirect("admin:index")

    incidents = Incident.objects.filter(created_by=request.user).order_by("-created_at")
    return render(request, "incidents/my_incidents.html", {"incidents": incidents})


@login_required
def incident_detail(request, incident_id):
    if request.user.is_staff:
        return redirect("admin:index")

    incident = get_incident_for_user(request.user, incident_id)
    comments = incident.comments.select_related("created_by").all()
    comment_form = IncidentCommentForm()
    return render(
        request,
        "incidents/incident_detail.html",
        {
            "incident": incident,
            "comments": comments,
            "comment_form": comment_form,
        },
    )


@login_required
def add_comment(request, incident_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    if request.user.is_staff:
        return redirect("admin:index")

    incident = get_incident_for_user(request.user, incident_id)
    form = IncidentCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.incident = incident
        comment.created_by = request.user
        comment.is_admin_note = False
        comment.save()
        messages.success(request, "Comment added.")
    else:
        messages.error(request, "Unable to add comment. Please check your input.")
    return redirect("incidents:detail", incident_id=incident.id)
