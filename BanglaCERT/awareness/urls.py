from django.urls import path
from . import views

app_name = "awareness"

urlpatterns = [
    path("", views.post_list, name="list"),
    path("<int:incident_id>/", views.post_detail, name="detail"),
    path("<int:incident_id>/like/", views.toggle_like, name="toggle_like"),
    path("<int:incident_id>/comment/", views.add_comment, name="add_comment"),
    path("<int:incident_id>/share/", views.share_post, name="share"),
]
