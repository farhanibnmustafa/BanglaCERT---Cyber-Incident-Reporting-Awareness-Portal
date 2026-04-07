"""
URL configuration for BangaCERT project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="incidents:home", permanent=False)),
    path("staff-login/", RedirectView.as_view(pattern_name="accounts:staff_login", permanent=False)),
    path("favicon.ico", RedirectView.as_view(url="/static/admin/img/BanglaCERT-logo.png", permanent=False)),
    path("admin/", include(("incidents.admin_urls", "admin"), namespace="admin")),
    path('accounts/', include('accounts.urls')),
    path('core/', include('core.urls')),
    path('incidents/', include('incidents.urls')),
    path('awareness/', include('awareness.urls')),
    path('analytics/', include('analytics.urls')),
    path('auditlog/', include('auditlog.urls')),
    path('notifications/', include('notifications.urls')),
    path('search/', include('search.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
