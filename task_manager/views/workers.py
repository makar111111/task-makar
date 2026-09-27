from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.views import generic

from task_manager.forms import WorkerCreationForm, WorkerUpdateForm
from task_manager.models import Project, Worker
from task_manager.views.mixins import (
    ConfirmDeleteMixin,
    ObjectMessageMixin,
    SearchMixin,
)


class WorkerListView(LoginRequiredMixin, SearchMixin, generic.ListView):
    model = Worker
    paginate_by = 12
    search_fields = ("username", "first_name", "last_name")
    search_placeholder = "Search by name or username..."
    queryset = (
        Worker.objects.select_related("position")
        .prefetch_related("teams")
        .annotate(
            num_open_tasks=Count(
                "tasks", filter=Q(tasks__is_completed=False)
            ),
            num_completed_tasks=Count(
                "tasks", filter=Q(tasks__is_completed=True)
            ),
        )
        .order_by("username")
    )


class WorkerDetailView(LoginRequiredMixin, generic.DetailView):
    model = Worker
    queryset = Worker.objects.select_related("position").prefetch_related(
        "teams"
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = self.object.tasks.select_related(
            "project", "task_type"
        ).prefetch_related("tags")
        context["open_tasks"] = tasks.filter(is_completed=False)
        context["completed_tasks"] = tasks.filter(is_completed=True)
        context["projects"] = Project.objects.filter(
            teams__members=self.object
        ).distinct()
        return context


class WorkerCreateView(
    LoginRequiredMixin, ObjectMessageMixin, generic.CreateView
):
    model = Worker
    form_class = WorkerCreationForm
    success_message = 'Worker "%(object)s" was created.'


class WorkerUpdateView(
    LoginRequiredMixin, ObjectMessageMixin, generic.UpdateView
):
    model = Worker
    form_class = WorkerUpdateForm
    success_message = 'Worker "%(object)s" was updated.'


class WorkerDeleteView(
    LoginRequiredMixin, ConfirmDeleteMixin, generic.DeleteView
):
    model = Worker
    success_url = reverse_lazy("task_manager:worker-list")

    def get_delete_warning(self):
        if self.object == self.request.user:
            return "This is your own account: you will be signed out."
        return ""
