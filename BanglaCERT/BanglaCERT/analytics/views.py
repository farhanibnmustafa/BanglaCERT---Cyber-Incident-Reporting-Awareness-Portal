from django.http import HttpResponseRedirect
from django.urls import reverse


def dashboard(request):
    return HttpResponseRedirect(f"{reverse('incidents:home')}#analytics")
