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
    path(
        "tasks/<int:pk>/toggle-assign/",
        views.toggle_task_assignment,
        name="task-toggle-assign",
    ),
    path(
        "tasks/<int:pk>/toggle-complete/",
        views.toggle_task_completion,
        name="task-toggle-complete",
    ),
    path("workers/", views.WorkerListView.as_view(), name="worker-list"),
    path(
        "workers/<int:pk>/",
        views.WorkerDetailView.as_view(),
        name="worker-detail",
    ),
    path(
        "workers/create/",
        views.WorkerCreateView.as_view(),
        name="worker-create",
    ),
    path(
        "workers/<int:pk>/update/",
        views.WorkerUpdateView.as_view(),
        name="worker-update",
    ),
    path(
        "workers/<int:pk>/delete/",
        views.WorkerDeleteView.as_view(),
        name="worker-delete",
    ),
    path("projects/", views.ProjectListView.as_view(), name="project-list"),
    path(
        "projects/<int:pk>/",
        views.ProjectDetailView.as_view(),
        name="project-detail",
    ),
    path(
        "projects/create/",
        views.ProjectCreateView.as_view(),
        name="project-create",
    ),
    path(
        "projects/<int:pk>/update/",
        views.ProjectUpdateView.as_view(),
        name="project-update",
    ),
    path(
        "projects/<int:pk>/delete/",
        views.ProjectDeleteView.as_view(),
        name="project-delete",
    ),
    path("teams/", views.TeamListView.as_view(), name="team-list"),
    path(
        "teams/<int:pk>/", views.TeamDetailView.as_view(), name="team-detail"
    ),
    path(
        "teams/create/", views.TeamCreateView.as_view(), name="team-create"
    ),
    path(
        "teams/<int:pk>/update/",
        views.TeamUpdateView.as_view(),
        name="team-update",
    ),
    path(
        "teams/<int:pk>/delete/",
        views.TeamDeleteView.as_view(),
        name="team-delete",
    ),
    path(
        "teams/<int:pk>/toggle-membership/",
        views.toggle_team_membership,
        name="team-toggle-membership",
    ),
    path(
        "positions/",
        views.PositionListView.as_view(),
        name="position-list",
    ),
    path(
        "positions/create/",
        views.PositionCreateView.as_view(),
        name="position-create",
    ),
    path(
        "positions/<int:pk>/update/",
        views.PositionUpdateView.as_view(),
        name="position-update",
    ),
    path(
        "positions/<int:pk>/delete/",
        views.PositionDeleteView.as_view(),
        name="position-delete",
    ),
    path(
        "task-types/",
        views.TaskTypeListView.as_view(),
        name="tasktype-list",
    ),
    path(
        "task-types/create/",
        views.TaskTypeCreateView.as_view(),
        name="tasktype-create",
    ),
    path(
        "task-types/<int:pk>/update/",
        views.TaskTypeUpdateView.as_view(),
        name="tasktype-update",
    ),
    path(
        "task-types/<int:pk>/delete/",
        views.TaskTypeDeleteView.as_view(),
        name="tasktype-delete",
    ),
    path(
        "tags/",
        views.TagListView.as_view(),
        name="tag-list",
    ),
    path(
        "tags/create/",
        views.TagCreateView.as_view(),
        name="tag-create",
    ),
    path(
        "tags/<int:pk>/update/",
        views.TagUpdateView.as_view(),
        name="tag-update",
    ),
    path(
        "tags/<int:pk>/delete/",
        views.TagDeleteView.as_view(),
        name="tag-delete",
    ),
]
