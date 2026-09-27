from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, ProtectedError
from django.shortcuts import redirect
from django.template.defaultfilters import pluralize
from django.urls import reverse
from django.views import generic

from task_manager.models import Position, Tag, TaskType
from task_manager.views.mixins import (
    ConfirmDeleteMixin,
    ObjectMessageMixin,
    SearchMixin,
)

# Positions, task types and tags have only a name, so they share
# the same templates. DIRECTORIES describes how to show each of them.
DIRECTORIES = {
    Position: {
        "url_prefix": "position",
        "title": "Positions",
        "description": "Roles of workers: developer, designer, QA...",
        "icon": "bi-briefcase",
        "count_relation": "workers",
        "count_label": "worker",
        "filter_param": "",
        "hint": "",
    },
    TaskType: {
        "url_prefix": "tasktype",
        "title": "Task types",
        "description": "Kinds of work: bugs, new features, refactoring...",
        "icon": "bi-bookmark",
        "count_relation": "tasks",
        "count_label": "task",
        "filter_param": "task_type",
        "hint": "",
    },
    Tag: {
        "url_prefix": "tag",
        "title": "Tags",
        "description": "Labels that group tasks across projects.",
        "icon": "bi-tags",
        "count_relation": "tasks",
        "count_label": "task",
        "filter_param": "tag",
        "hint": (
            "Use kebab-case: lowercase letters and digits separated by "
            "hyphens, e.g. landing-page-layout."
        ),
    },
}


class DirectoryMixin:
    def get_directory(self):
        return DIRECTORIES[self.model]

    def get_list_url(self):
        url_prefix = self.get_directory()["url_prefix"]
        return reverse(f"task_manager:{url_prefix}-list")

    def get_success_url(self):
        return self.get_list_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        url_prefix = self.get_directory()["url_prefix"]
        context["directory"] = self.get_directory() | {
            "singular": self.model._meta.verbose_name,
            "list_url": self.get_list_url(),
            "create_url": reverse(f"task_manager:{url_prefix}-create"),
            "update_url_name": f"task_manager:{url_prefix}-update",
            "delete_url_name": f"task_manager:{url_prefix}-delete",
        }
        return context


class DirectoryListMixin(DirectoryMixin, SearchMixin):
    template_name = "task_manager/directory_list.html"
    paginate_by = 10

    def get_queryset(self):
        relation = self.get_directory()["count_relation"]
        return (
            super()
            .get_queryset()
            .annotate(num_related=Count(relation))
            .order_by("name")
        )


class DirectoryFormMixin(DirectoryMixin, ObjectMessageMixin):
    template_name = "task_manager/directory_form.html"
    fields = ("name",)
    success_message = '"%(object)s" was saved.'


class DirectoryDeleteMixin(DirectoryMixin, ConfirmDeleteMixin):
    def get_delete_warning(self):
        directory = self.get_directory()
        num_related = getattr(self.object, directory["count_relation"]).count()
        if not num_related:
            return ""
        return self.get_related_warning(
            f"{num_related} {directory['count_label']}"
            f"{pluralize(num_related)}"
        )

    def get_related_warning(self, related):
        return f"It will be removed from {related}."


class PositionListView(
    LoginRequiredMixin, DirectoryListMixin, generic.ListView
):
    model = Position


class PositionCreateView(
    LoginRequiredMixin, DirectoryFormMixin, generic.CreateView
):
    model = Position


class PositionUpdateView(
    LoginRequiredMixin, DirectoryFormMixin, generic.UpdateView
):
    model = Position


class PositionDeleteView(
    LoginRequiredMixin, DirectoryDeleteMixin, generic.DeleteView
):
    model = Position

    def get_related_warning(self, related):
        return f"{related} will stay without a position."


class TaskTypeListView(
    LoginRequiredMixin, DirectoryListMixin, generic.ListView
):
    model = TaskType


class TaskTypeCreateView(
    LoginRequiredMixin, DirectoryFormMixin, generic.CreateView
):
    model = TaskType


class TaskTypeUpdateView(
    LoginRequiredMixin, DirectoryFormMixin, generic.UpdateView
):
    model = TaskType


class TaskTypeDeleteView(
    LoginRequiredMixin, DirectoryDeleteMixin, generic.DeleteView
):
    model = TaskType

    def get_related_warning(self, related):
        return (
            f"{related} of this type exist. Change their type first: "
            "a task type in use can't be deleted."
        )

    def can_delete(self):
        return not self.object.tasks.exists()

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.error(
                self.request,
                f'"{self.object}" is used by tasks and cannot be deleted.',
            )
            return redirect(self.get_success_url())


class TagListView(LoginRequiredMixin, DirectoryListMixin, generic.ListView):
    model = Tag


class TagCreateView(
    LoginRequiredMixin, DirectoryFormMixin, generic.CreateView
):
    model = Tag


class TagUpdateView(
    LoginRequiredMixin, DirectoryFormMixin, generic.UpdateView
):
    model = Tag


class TagDeleteView(
    LoginRequiredMixin, DirectoryDeleteMixin, generic.DeleteView
):
    model = Tag
