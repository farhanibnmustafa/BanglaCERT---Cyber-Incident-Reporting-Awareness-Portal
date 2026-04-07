from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import AwarenessCommentForm
from .models import AwarenessComment, AwarenessLike, AwarenessShare
from .services import (
    get_public_incidents_queryset,
    prepare_public_incident,
    prepare_public_incidents,
)


def _get_public_incident(incident_id):
    return get_object_or_404(get_public_incidents_queryset(), id=incident_id)


def _redirect_back_or_detail(request, incident_id):
    return_url = (
        request.POST.get("next")
        or request.GET.get("next")
        or request.META.get("HTTP_REFERER", "")
    ).strip()
    if return_url and url_has_allowed_host_and_scheme(
        url=return_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(return_url)
    return redirect("awareness:detail", incident_id=incident_id)


def post_list(request):
    incidents = prepare_public_incidents(
        get_public_incidents_queryset(),
        user=request.user,
    )
    return render(request, "awareness/post_list.html", {"incidents": incidents})


def post_detail(request, incident_id):
    incident = prepare_public_incident(_get_public_incident(incident_id), user=request.user)
    comments = AwarenessComment.objects.filter(incident=incident).select_related("created_by")
    context = {
        "incident": incident,
        "comments": comments,
        "comment_form": AwarenessCommentForm(),
        "share_url": request.build_absolute_uri(reverse("awareness:detail", args=[incident.id])),
    }
    return render(request, "awareness/post_detail.html", context)


@login_required
def toggle_like(request, incident_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    incident = _get_public_incident(incident_id)
    like, created = AwarenessLike.objects.get_or_create(incident=incident, created_by=request.user)
    if created:
        messages.success(request, "Post liked.")
    else:
        like.delete()
        messages.success(request, "Like removed.")
    return _redirect_back_or_detail(request, incident.id)


@login_required
def add_comment(request, incident_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    incident = _get_public_incident(incident_id)
    form = AwarenessCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.incident = incident
        comment.created_by = request.user
        comment.save()
        messages.success(request, "Comment added.")
    else:
        messages.error(request, "Unable to add comment. Please check your input.")
    return redirect("awareness:detail", incident_id=incident.id)


def share_post(request, incident_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    incident = _get_public_incident(incident_id)
    AwarenessShare.objects.create(
        incident=incident,
        shared_by=request.user if request.user.is_authenticated else None,
    )
    messages.success(
        request,
        f"Share this verified post with this link: {request.build_absolute_uri(reverse('awareness:detail', args=[incident.id]))}",
    )
    return _redirect_back_or_detail(request, incident.id)
