from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic
from django.views.decorators.http import require_POST

from task_manager.forms import TaskFilterForm, TaskForm
from task_manager.models import Task
from task_manager.views.mixins import (
    ConfirmDeleteMixin,
    ObjectMessageMixin,
    redirect_back,
)


def get_task_counts():
    today = timezone.localdate()
    return Task.objects.aggregate(
        num_open=Count("pk", filter=Q(is_completed=False)),
        num_completed=Count("pk", filter=Q(is_completed=True)),
        num_overdue=Count(
            "pk", filter=Q(is_completed=False, deadline__lt=today)
        ),
    )


class TaskListView(LoginRequiredMixin, generic.ListView):
    model = Task
    paginate_by = 10
    queryset = Task.objects.select_related(
        "project", "task_type"
    ).prefetch_related("tags", "assignees")

    def get_queryset(self):
        self.filter_form = TaskFilterForm(self.request.GET)
        return self.filter_form.filter_queryset(super().get_queryset())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter_form"] = self.filter_form
        context["status"] = self.filter_form.get_status()
        context["status_choices"] = TaskFilterForm.STATUS_CHOICES
        context["task_counts"] = get_task_counts()
        return context


class TaskDetailView(LoginRequiredMixin, generic.DetailView):
    model = Task
    queryset = Task.objects.select_related(
        "project", "task_type"
    ).prefetch_related("tags", "assignees__position")


class TaskCreateView(
    LoginRequiredMixin, ObjectMessageMixin, generic.CreateView
):
    model = Task
    form_class = TaskForm
    success_message = 'Task "%(object)s" was created.'

    def get_initial(self):
        """Preselect the project when the task is added from its page."""
        initial = super().get_initial()
        if "project" in self.request.GET:
            initial["project"] = self.request.GET["project"]
        return initial


class TaskUpdateView(
    LoginRequiredMixin, ObjectMessageMixin, generic.UpdateView
):
    model = Task
    form_class = TaskForm
    success_message = 'Task "%(object)s" was updated.'


class TaskDeleteView(
    LoginRequiredMixin, ConfirmDeleteMixin, generic.DeleteView
):
    model = Task
    success_url = reverse_lazy("task_manager:task-list")


@login_required
@require_POST
def toggle_task_assignment(request, pk):
    # The task row stays locked until the transaction ends, so parallel
    # requests (a double click, two tabs) change the task one by one
    with transaction.atomic():
        task = get_object_or_404(Task.objects.select_for_update(), pk=pk)
        if task.assignees.filter(pk=request.user.pk).exists():
            task.assignees.remove(request.user)
            messages.info(request, f'You are no longer assigned to "{task}".')
        else:
            task.assignees.add(request.user)
            messages.success(request, f'You are assigned to "{task}".')
    return redirect_back(request, task.get_absolute_url())


@login_required
@require_POST
def toggle_task_completion(request, pk):
    # The task row stays locked until the transaction ends, so parallel
    # requests (a double click, two tabs) change the task one by one
    with transaction.atomic():
        task = get_object_or_404(Task.objects.select_for_update(), pk=pk)
        task.is_completed = not task.is_completed
        task.save(update_fields=["is_completed"])
    if task.is_completed:
        messages.success(request, f'"{task}" is completed. Nice work!')
    else:
        messages.info(request, f'"{task}" is open again.')
    return redirect_back(request, task.get_absolute_url())
