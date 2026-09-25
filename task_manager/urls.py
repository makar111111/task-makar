from django.urls import path

from task_manager import views

app_name = "task_manager"

urlpatterns = [
    path("", views.index, name="index"),
]
