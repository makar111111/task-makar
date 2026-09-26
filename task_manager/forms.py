from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone

from task_manager.models import Project, Tag, Task, TaskType, Worker


class SearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, placeholder="Search...", **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["search"].widget.attrs["placeholder"] = placeholder


class WorkerProfileFieldsMixin:
    """Makes the name and the email required for workers."""

    required_fields = ("first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.required_fields:
            self.fields[field_name].required = True
        self.fields["position"].empty_label = "No position"


class WorkerCreationForm(WorkerProfileFieldsMixin, UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Worker
        fields = UserCreationForm.Meta.fields + (
            "first_name",
            "last_name",
            "email",
            "position",
        )


class WorkerUpdateForm(WorkerProfileFieldsMixin, forms.ModelForm):
    class Meta:
        model = Worker
        fields = ("first_name", "last_name", "email", "position")


class WorkerLabelMixin:
    """Shows workers by full name instead of "username (Full Name)"."""

    def label_from_instance(self, obj):
        return obj.get_full_name() or obj.username


class WorkerChoiceField(WorkerLabelMixin, forms.ModelChoiceField):
    pass


class WorkerMultipleChoiceField(
    WorkerLabelMixin, forms.ModelMultipleChoiceField
):
    pass


class TaskForm(forms.ModelForm):
    assignees = WorkerMultipleChoiceField(
        queryset=get_user_model().objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "form-check-input"}
        ),
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(
            attrs={"class": "form-check-input"}
        ),
    )

    class Meta:
        model = Task
        fields = (
            "name",
            "description",
            "project",
            "task_type",
            "priority",
            "deadline",
            "assignees",
            "tags",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "deadline": forms.DateInput(
                attrs={"type": "date"}, format="%Y-%m-%d"
            ),
        }

    def clean_deadline(self):
        """A new deadline can't be in the past.

        An old deadline of an existing task may stay as it is, otherwise
        overdue tasks couldn't be edited at all.
        """
        deadline = self.cleaned_data["deadline"]
        if "deadline" in self.changed_data and deadline < timezone.localdate():
            raise ValidationError("The deadline can't be in the past.")
        return deadline


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
