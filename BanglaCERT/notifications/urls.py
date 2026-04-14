from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path('api/latest/', views.get_notifications, name='get_latest'),
    path('api/mark-read/', views.mark_all_read, name='mark_read'),
]
