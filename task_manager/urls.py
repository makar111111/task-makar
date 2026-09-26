from django.urls import path

from task_manager import views

app_name = "task_manager"

urlpatterns = [
    path("", views.index, name="index"),
    path("tasks/", views.TaskListView.as_view(), name="task-list"),
    path(
        "tasks/<int:pk>/", views.TaskDetailView.as_view(), name="task-detail"
    ),
    path(
        "tasks/create/", views.TaskCreateView.as_view(), name="task-create"
    ),
    path(
        "tasks/<int:pk>/update/",
        views.TaskUpdateView.as_view(),
        name="task-update",
    ),
    path(
        "tasks/<int:pk>/delete/",
        views.TaskDeleteView.as_view(),
        name="task-delete",
    ),
]
