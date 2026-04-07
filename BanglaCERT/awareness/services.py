import re

from django.db.models import Count
from django.utils.text import Truncator

from incidents.models import Incident

from .models import AwarenessLike


CONFIDENTIAL_REPLACEMENTS = [
    (re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE), "[hidden email]"),
    (re.compile(r"\b(?:https?://|www\.)\S+\b", re.IGNORECASE), "[hidden link]"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[hidden ip]"),
    (re.compile(r"(?<!\w)(?:\+?\d[\d\s-]{7,}\d)(?!\w)"), "[hidden phone]"),
    (re.compile(r"\b\d{8,}\b"), "[hidden number]"),
]


def mask_confidential_text(text):
    masked_text = text or ""
    for pattern, replacement in CONFIDENTIAL_REPLACEMENTS:
        masked_text = pattern.sub(replacement, masked_text)
    return masked_text


def get_public_incidents_queryset():
    return (
        Incident.objects.filter(status=Incident.STATUS_VERIFIED)
        .annotate(
            likes_total=Count("awareness_likes", distinct=True),
            comments_total=Count("awareness_comments", distinct=True),
            shares_total=Count("awareness_shares", distinct=True),
        )
        .order_by("-updated_at", "-created_at")
    )


def prepare_public_incidents(incidents, user=None):
    incidents = list(incidents)
    liked_ids = set()

    if user and user.is_authenticated:
        liked_ids = set(
            AwarenessLike.objects.filter(
                created_by=user,
                incident_id__in=[incident.id for incident in incidents],
            ).values_list("incident_id", flat=True)
        )

    for incident in incidents:
        incident.public_title = mask_confidential_text(incident.title)
        incident.public_description = mask_confidential_text(incident.description)
        incident.public_excerpt = Truncator(incident.public_description).words(40, truncate="...")
        incident.user_has_liked = incident.id in liked_ids
    return incidents


def prepare_public_incident(incident, user=None):
    prepared_incidents = prepare_public_incidents([incident], user=user)
    return prepared_incidents[0]
