from django.shortcuts import redirect, render

from .forms import IncidentPublicReportForm


def public_report_incident(request):
    if request.method == "POST":
        form = IncidentPublicReportForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)
            if request.user.is_authenticated and not incident.is_anonymous:
                incident.created_by = request.user
            else:
                incident.created_by = None
                incident.is_anonymous = True
            incident.save()
            return redirect("incidents:report_success")
    else:
        form = IncidentPublicReportForm()

    return render(request, "incidents/report_incident.html", {"form": form})


def public_report_success(request):
    return render(request, "incidents/report_success.html")
