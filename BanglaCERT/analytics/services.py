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


def _build_smooth_path(points, tension=0.4):
    """
    Convert raw (x, y) points to a smooth SVG cubic bezier path string
    using a cardinal spline algorithm.
    Returns (open_path, closed_area_path).
    open_path  = smooth line  (for the stroke)
    closed_area_path = closed polygon (for the filled area under the line)
    """
    if not points:
        return "", ""
    if len(points) == 1:
        p = points[0]
        return f"M {p['x']},{p['y']}", f"M {p['x']},130 L {p['x']},{p['y']} L {p['x']},130 Z"

    pts = [(p["x"], p["y"]) for p in points]
    n = len(pts)

    path = f"M {pts[0][0]},{pts[0][1]}"
    for i in range(1, n):
        p0 = pts[i - 2] if i >= 2 else pts[0]
        p1 = pts[i - 1]
        p2 = pts[i]
        p3 = pts[i + 1] if i < n - 1 else pts[-1]

        cp1x = p1[0] + (p2[0] - p0[0]) * tension
        cp1y = p1[1] + (p2[1] - p0[1]) * tension
        cp2x = p2[0] - (p3[0] - p1[0]) * tension
        cp2y = p2[1] - (p3[1] - p1[1]) * tension

        path += f" C {cp1x:.2f},{cp1y:.2f} {cp2x:.2f},{cp2y:.2f} {p2[0]},{p2[1]}"

    # Closed area path: go down to baseline, back to start
    area = path + f" L {pts[-1][0]},130 L {pts[0][0]},130 Z"

    return path, area


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
    total_reported = Incident.objects.count()   # ALL reports regardless of status
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

    # Smooth bezier path for the glossy curved chart
    smooth_path, smooth_area_path = _build_smooth_path(frequency_points)

    most_common_type = category_breakdown[0]["label"] if category_breakdown else "No data"

    return {
        "total_incidents": total_incidents,
        "total_reported": total_reported,
        "verified_incidents": verified_incidents,
        "public_posts": verified_incidents,
        "most_common_type": most_common_type,
        "category_breakdown": category_breakdown,
        "frequency_points": frequency_points,
        "frequency_line_points": line_points,
        "frequency_smooth_path": smooth_path,
        "frequency_smooth_area": smooth_area_path,
        "analyzed_label": analyzed_label,
        "analytics_scope": scope,
    }
