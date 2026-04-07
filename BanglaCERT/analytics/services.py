from collections import Counter

from incidents.models import Incident


def _build_frequency_series(incidents):
    monthly_counts = {}
    for incident in incidents:
        label = incident.incident_date.strftime("%b %Y")
        monthly_counts[label] = monthly_counts.get(label, 0) + 1

    items = [{"label": label, "count": count} for label, count in monthly_counts.items()]
    max_count = max((item["count"] for item in items), default=1)
    total_points = len(items)
    step = 260 / max(total_points - 1, 1)

    for index, item in enumerate(items):
        item["height"] = max(12, int((item["count"] / max_count) * 120)) if item["count"] else 0
        item["x"] = round(20 + (index * step), 2)
        item["y"] = round(130 - ((item["count"] / max_count) * 90), 2)

    return items


def build_analytics_dashboard(*, scope="verified"):
    if scope == "all":
        incidents = list(Incident.objects.order_by("incident_date", "created_at"))
        analyzed_label = "Reported Incidents Analyzed"
    else:
        incidents = list(
            Incident.objects.filter(status=Incident.STATUS_VERIFIED).order_by("incident_date", "created_at")
        )
        analyzed_label = "Verified Posts Analyzed"

    total_incidents = len(incidents)
    verified_incidents = sum(1 for incident in incidents if incident.status == Incident.STATUS_VERIFIED)

    category_counter = Counter(incident.get_category_display() for incident in incidents)
    max_category_total = max(category_counter.values(), default=1)
    category_breakdown = [
        {
            "label": label,
            "count": count,
            "width": int((count / max_category_total) * 100) if max_category_total else 0,
        }
        for label, count in category_counter.most_common()
    ]

    frequency_points = _build_frequency_series(incidents)
    line_points = " ".join(f"{item['x']},{item['y']}" for item in frequency_points)
    most_common_type = category_breakdown[0]["label"] if category_breakdown else "No data"

    return {
        "total_incidents": total_incidents,
        "verified_incidents": verified_incidents,
        "public_posts": verified_incidents,
        "most_common_type": most_common_type,
        "category_breakdown": category_breakdown,
        "frequency_points": frequency_points,
        "frequency_line_points": line_points,
        "analyzed_label": analyzed_label,
        "analytics_scope": scope,
    }
