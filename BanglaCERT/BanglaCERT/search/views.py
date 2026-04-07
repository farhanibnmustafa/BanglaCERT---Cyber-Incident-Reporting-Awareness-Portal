from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .filters import PublicIncidentSearchForm
from .services import search_public_incidents


def incident_search(request):
    form = PublicIncidentSearchForm(request.GET or None)
    incidents = search_public_incidents(form, user=request.user)
    context = {
        "form": form,
        "incidents": incidents,
    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return render(request, "search/_results.html", context)

    query_string = request.GET.urlencode()
    target = reverse("incidents:home")
    if query_string:
        target = f"{target}?{query_string}#awareness"
    else:
        target = f"{target}#awareness"
    return HttpResponseRedirect(target)
