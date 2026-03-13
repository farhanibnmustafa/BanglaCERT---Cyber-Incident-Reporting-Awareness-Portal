from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("staff-login/", views.staff_login_view, name="staff_login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="accounts:login"), name="logout"),
]
