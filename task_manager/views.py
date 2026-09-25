from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils import timezone

from task_manager.models import Project, Task, Team, Worker


def get_greeting(hour):
    if hour < 12:
        return "Good morning"
    if hour < 18:
        return "Good afternoon"
    return "Good evening"


@login_required
def index(request):
    """Dashboard: task counters, open tasks of the user, project progress."""
    today = timezone.localdate()

    num_visits = request.session.get("num_visits", 0) + 1
    request.session["num_visits"] = num_visits

    task_counts = Task.objects.aggregate(
        num_open=Count("pk", filter=Q(is_completed=False)),
        num_completed=Count("pk", filter=Q(is_completed=True)),
        num_overdue=Count(
            "pk", filter=Q(is_completed=False, deadline__lt=today)
        ),
    )
    num_all_tasks = task_counts["num_open"] + task_counts["num_completed"]
    my_open_tasks = request.user.tasks.filter(is_completed=False)

    context = {
        **task_counts,
        "completed_percent": (
            round(task_counts["num_completed"] * 100 / num_all_tasks)
            if num_all_tasks
            else 0
        ),
        "num_projects": Project.objects.count(),
        "num_teams": Team.objects.count(),
        "num_workers": Worker.objects.count(),
        "num_my_open_tasks": my_open_tasks.count(),
        "num_my_overdue_tasks": my_open_tasks.filter(
            deadline__lt=today
        ).count(),
        "my_tasks": my_open_tasks.select_related(
            "project", "task_type"
        ).prefetch_related("tags")[:5],
        "projects": Project.objects.annotate(
            num_tasks=Count("tasks"),
            num_completed_tasks=Count(
                "tasks", filter=Q(tasks__is_completed=True)
            ),
        ).prefetch_related("teams__members")[:4],
        "greeting": get_greeting(timezone.localtime().hour),
        "num_visits": num_visits,
    }
    return render(request, "task_manager/index.html", context=context)
