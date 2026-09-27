from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.template.defaultfilters import pluralize
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic

from task_manager.forms import ProjectForm
from task_manager.models import Project
from task_manager.views.mixins import (
    ConfirmDeleteMixin,
    ObjectMessageMixin,
    SearchMixin,
)


def annotate_task_counts(projects):
    today = timezone.localdate()
    return projects.annotate(
        num_tasks=Count("tasks", distinct=True),
        num_completed_tasks=Count(
            "tasks", filter=Q(tasks__is_completed=True), distinct=True
        ),
        num_overdue_tasks=Count(
            "tasks",
            filter=Q(tasks__is_completed=False, tasks__deadline__lt=today),
            distinct=True,
        ),
    )


class ProjectListView(LoginRequiredMixin, SearchMixin, generic.ListView):
    model = Project
    paginate_by = 9

    def get_queryset(self):
        projects = annotate_task_counts(super().get_queryset())
        return projects.order_by("name").prefetch_related("teams__members")


class ProjectDetailView(LoginRequiredMixin, generic.DetailView):
    model = Project

    def get_queryset(self):
        return annotate_task_counts(Project.objects.all()).prefetch_related(
            "teams__members"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = self.object.tasks.select_related(
            "project", "task_type"
        ).prefetch_related("tags")
        context["open_tasks"] = tasks.filter(is_completed=False)
        context["completed_tasks"] = tasks.filter(is_completed=True)
        return context


class ProjectCreateView(
    LoginRequiredMixin, ObjectMessageMixin, generic.CreateView
):
    model = Project
    form_class = ProjectForm
    success_message = 'Project "%(object)s" was created.'


class ProjectUpdateView(
    LoginRequiredMixin, ObjectMessageMixin, generic.UpdateView
):
    model = Project
    form_class = ProjectForm
    success_message = 'Project "%(object)s" was updated.'


class ProjectDeleteView(
    LoginRequiredMixin, ConfirmDeleteMixin, generic.DeleteView
):
    model = Project
    success_url = reverse_lazy("task_manager:project-list")

    def get_delete_warning(self):
        num_tasks = self.object.tasks.count()
        if num_tasks:
            return (
                f"{num_tasks} task{pluralize(num_tasks)} of this project "
                "will be deleted too."
            )
        return ""
