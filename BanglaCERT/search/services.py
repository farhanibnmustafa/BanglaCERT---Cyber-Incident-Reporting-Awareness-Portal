from awareness.services import get_public_incidents_queryset, prepare_public_incidents


def search_public_incidents(form, user=None):
    incidents = get_public_incidents_queryset()

    if form.is_valid():
        category = form.cleaned_data.get("category")
        date_from = form.cleaned_data.get("date_from")
        date_to = form.cleaned_data.get("date_to")

        if category:
            incidents = incidents.filter(category=category)
        if date_from:
            incidents = incidents.filter(incident_date__gte=date_from)
        if date_to:
            incidents = incidents.filter(incident_date__lte=date_to)

    public_incidents = prepare_public_incidents(incidents, user=user)
    query = ""
    if form.is_valid():
        query = (form.cleaned_data.get("q") or "").strip().lower()

    if not query:
        return public_incidents

    return [
        incident
        for incident in public_incidents
        if query in incident.public_title.lower() or query in incident.public_description.lower()
    ]
