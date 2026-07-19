from django.urls import path

from . import views

app_name = "adminpanel"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("users/", views.user_list, name="user_list"),
    path("users/new/", views.user_create, name="user_create"),
    path("users/<int:user_id>/toggle-active/", views.user_toggle_active, name="user_toggle_active"),
    path("logs/", views.logs, name="logs"),
]
