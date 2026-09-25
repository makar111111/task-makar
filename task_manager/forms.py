from django import forms
from django.contrib.auth import get_user_model

from task_manager.models import Project, Tag, Task, TaskType


class WorkerChoiceField(forms.ModelChoiceField):
    """Shows workers by full name instead of "username (Full Name)"."""

    def label_from_instance(self, obj):
        return obj.get_full_name() or obj.username


class TaskFilterForm(forms.Form):
    """Search and filters of the task list, read from GET parameters."""

    STATUS_OPEN = "open"
    STATUS_COMPLETED = "completed"
    STATUS_ALL = "all"
    STATUS_CHOICES = (
        (STATUS_OPEN, "Open"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_ALL, "All"),
    )

    search = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Search by name..."}
        ),
    )
    priority = forms.ChoiceField(
        required=False,
        choices=[("", "All priorities"), *Task.Priority.choices],
        widget=forms.Select(attrs={"class": "form-select w-auto"}),
    )
    task_type = forms.ModelChoiceField(
        queryset=TaskType.objects.all(),
        required=False,
        empty_label="All types",
        widget=forms.Select(attrs={"class": "form-select w-auto"}),
    )
    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        required=False,
        empty_label="All projects",
        widget=forms.Select(attrs={"class": "form-select w-auto"}),
    )
    tag = forms.ModelChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        empty_label="All tags",
        widget=forms.Select(attrs={"class": "form-select w-auto"}),
    )
    assignee = WorkerChoiceField(
        queryset=get_user_model().objects.all(),
        required=False,
        empty_label="All assignees",
        widget=forms.Select(attrs={"class": "form-select w-auto"}),
    )
    status = forms.ChoiceField(required=False, choices=STATUS_CHOICES)

    def get_status(self):
        """Selected status; open tasks are shown by default."""
        self.is_valid()
        return self.cleaned_data.get("status") or self.STATUS_OPEN

    def filter_queryset(self, queryset):
        """Apply the valid filters, invalid values are ignored."""
        self.is_valid()
        filters = self.cleaned_data
        if filters.get("search"):
            queryset = queryset.filter(name__icontains=filters["search"])
        if filters.get("priority"):
            queryset = queryset.filter(priority=filters["priority"])
        if filters.get("task_type"):
            queryset = queryset.filter(task_type=filters["task_type"])
        if filters.get("project"):
            queryset = queryset.filter(project=filters["project"])
        if filters.get("tag"):
            queryset = queryset.filter(tags=filters["tag"])
        if filters.get("assignee"):
            queryset = queryset.filter(assignees=filters["assignee"])

        status = self.get_status()
        if status == self.STATUS_OPEN:
            queryset = queryset.filter(is_completed=False)
        elif status == self.STATUS_COMPLETED:
            queryset = queryset.filter(is_completed=True)
        return queryset
