from django.shortcuts import render, redirect
from .forms import IncidentReportForm


def report_incident(request):

    if request.method == "POST":
        form = IncidentReportForm(request.POST)

        if form.is_valid():
            incident = form.save(commit=False)

            if request.user.is_authenticated:
                incident.created_by = request.user

            incident.is_anonymous = form.cleaned_data[
                "report_anonymously"
            ]

            incident.save()

            return redirect("home")

    else:
        form = IncidentReportForm()

    return render(
        request,
        "incidents/report.html",
        {"form": form}
    )