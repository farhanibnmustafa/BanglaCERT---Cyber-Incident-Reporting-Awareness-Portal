from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import EmailLoginForm, UserRegistrationForm


def _redirect_by_role(user):
    if user.is_staff:
        return redirect("admin:index")
    return redirect("incidents:my_incidents")


def login_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    if request.method == "POST":
        form = EmailLoginForm(request.POST, request=request)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Signed in successfully.")
            return _redirect_by_role(user)
    else:
        form = EmailLoginForm(request=request)
    return render(request, "accounts/login.html", {"form": form})


def register(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Public registration creates normal users only.
            user.is_staff = False
            user.is_superuser = False
            user.save(update_fields=["is_staff", "is_superuser"])
            login(request, user)
            messages.success(request, "Registration completed. You can now submit incident reports.")
            return redirect("incidents:my_incidents")
    else:
        form = UserRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})
