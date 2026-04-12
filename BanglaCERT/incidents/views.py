import secrets

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from analytics.services import build_analytics_dashboard
from search.filters import PublicIncidentSearchForm
from search.services import search_public_incidents

from .forms import (
    AnonymousIncidentStatusLookupForm,
    IncidentCommentForm,
    IncidentPublicReportForm,
    IncidentReportForm,
)
from .models import Incident, IncidentEvidence
from notifications.services import notify_incident_submission


def get_incident_for_user(user, incident_id):
    return get_object_or_404(Incident, id=incident_id, created_by=user)


def _save_evidence_files(incident, uploaded_by, files):
    for evidence_file in files:
        IncidentEvidence.objects.create(
            incident=incident,
            file=evidence_file,
            original_name=evidence_file.name,
            uploaded_by=uploaded_by,
        )


def _issue_public_tracking_credentials(incident):
    updated_fields = incident.ensure_public_tracking_credentials()
    if updated_fields:
        incident.save(update_fields=updated_fields)


def _store_public_report_tracking(request, incident):
    request.session["public_report_tracking"] = {
        "tracking_id": incident.public_tracking_id,
        "access_token": incident.public_tracking_token,
        "reporter_email": incident.reporter_email,
    }


def _get_public_tracked_incident(tracking_id, access_token):
    incident = Incident.objects.filter(is_anonymous=True, public_tracking_id=tracking_id).first()
    if incident is None or not incident.public_tracking_token:
        return None
    if not secrets.compare_digest(incident.public_tracking_token, access_token):
        return None
    return incident


def home(request):
    if request.user.is_staff:
        return redirect("admin:index")

    search_form = PublicIncidentSearchForm(request.GET or None)
    awareness_incidents = search_public_incidents(search_form, user=request.user)
    context = {
        "search_form": search_form,
        "awareness_incidents": awareness_incidents,
        **build_analytics_dashboard(scope="verified"),
    }
    return render(request, "incidents/home.html", context)


@login_required
def report_incident(request):
    if request.user.is_staff:
        messages.info(request, "Staff users should manage incidents from the custom admin dashboard.")
        return redirect("admin:index")

    if request.method == "POST":
        form = IncidentReportForm(request.POST, request.FILES)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.created_by = request.user
            incident.is_anonymous = False
            if request.user.email:
                incident.reporter_email = request.user.email
            incident.save()
            _save_evidence_files(incident, request.user, form.cleaned_data.get("evidence_files", []))
            notify_incident_submission(incident)
            messages.success(request, "Incident submitted successfully.")
            return redirect("incidents:detail", incident_id=incident.id)
    else:
        form = IncidentReportForm()
    return render(request, "incidents/report_incident.html", {"form": form})


def public_report_incident(request):
    if request.method == "POST":
        form = IncidentPublicReportForm(request.POST, request.FILES)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.created_by = None
            incident.is_anonymous = True
            incident.save()
            _issue_public_tracking_credentials(incident)
            _save_evidence_files(incident, None, form.cleaned_data.get("evidence_files", []))
            _store_public_report_tracking(request, incident)
            notify_incident_submission(incident)
            messages.success(request, "Incident submitted successfully.")
            return redirect("incidents:public_report_success")
    else:
        form = IncidentPublicReportForm()
    return render(request, "incidents/public_report_incident.html", {"form": form})


def public_report_success(request):
    return render(
        request,
        "incidents/report_success.html",
        {"tracking": request.session.get("public_report_tracking")},
    )


def public_report_status(request):
    stored_tracking = request.session.get("public_report_tracking") or {}
    incident = None

    if request.method == "POST":
        form = AnonymousIncidentStatusLookupForm(request.POST)
        if form.is_valid():
            incident = _get_public_tracked_incident(
                tracking_id=form.cleaned_data["tracking_id"],
                access_token=form.cleaned_data["access_token"],
            )
            if incident is None:
                form.add_error(None, "Tracking ID or access token is invalid.")
    else:
        form = AnonymousIncidentStatusLookupForm(
            initial={
                "tracking_id": stored_tracking.get("tracking_id", ""),
                "access_token": stored_tracking.get("access_token", ""),
            }
        )

    return render(
        request,
        "incidents/public_report_status.html",
        {
            "form": form,
            "incident": incident,
        },
    )


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
    evidence_files = incident.evidence_files.all()
    comment_form = IncidentCommentForm()
    return render(
        request,
        "incidents/incident_detail.html",
        {
            "incident": incident,
            "comments": comments,
            "comment_form": comment_form,
            "evidence_files": evidence_files,
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
