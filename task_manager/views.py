from django.conf import settings
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import pluralize
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views import generic
from django.views.decorators.http import require_POST

from task_manager.demo import DEMO_PASSWORD, DEMO_USERNAME
from task_manager.forms import (
    ProjectForm,
    SearchForm,
    TaskFilterForm,
    TaskForm,
    TeamForm,
    WorkerCreationForm,
    WorkerUpdateForm,
)
from task_manager.models import (
    Position,
    Project,
    Tag,
    Task,
    TaskType,
    Team,
    Worker,
)


class SearchMixin:
    """Filters a list view by the "search" GET parameter."""

    search_fields = ("name",)
    search_placeholder = "Search by name..."

    def get_queryset(self):
        queryset = super().get_queryset()
        self.search_form = SearchForm(
            self.request.GET, placeholder=self.search_placeholder
        )
        if self.search_form.is_valid():
            query = self.search_form.cleaned_data["search"]
            if query:
                conditions = Q()
                for field in self.search_fields:
                    conditions |= Q(**{f"{field}__icontains": query})
                queryset = queryset.filter(conditions)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = self.search_form
        return context


class ObjectMessageMixin(SuccessMessageMixin):
    """Success message with the saved or deleted object, e.g.
    'Task "Fix login" was created.' Works for delete views too, where
    the form has no cleaned data about the object."""

    def get_success_message(self, cleaned_data):
        return self.success_message % {"object": self.object}


class ConfirmDeleteMixin(ObjectMessageMixin):
    """Shared confirmation page for all delete views."""

    template_name = "task_manager/confirm_delete.html"
    success_message = '"%(object)s" was deleted.'

    def get_cancel_url(self):
        if hasattr(self.object, "get_absolute_url"):
            return self.object.get_absolute_url()
        return self.get_success_url()

    def get_delete_warning(self):
        return ""

    def can_delete(self):
        return True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object_type"] = self.model._meta.verbose_name
        context["cancel_url"] = self.get_cancel_url()
        context["delete_warning"] = self.get_delete_warning()
        context["can_delete"] = self.can_delete()
        return context


def get_task_counts():
    today = timezone.localdate()
    return Task.objects.aggregate(
        num_open=Count("pk", filter=Q(is_completed=False)),
        num_completed=Count("pk", filter=Q(is_completed=True)),
        num_overdue=Count(
            "pk", filter=Q(is_completed=False, deadline__lt=today)
        ),
    )


class LoginView(auth_views.LoginView):
    """Login page that shows the demo account when DEMO_MODE is on."""

    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if settings.DEMO_MODE:
            context["demo_credentials"] = {
                "username": DEMO_USERNAME,
                "password": DEMO_PASSWORD,
            }
        return context


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

    task_counts = get_task_counts()
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
        )
        .order_by("name")
        .prefetch_related("teams__members")[:4],
        "greeting": get_greeting(timezone.localtime().hour),
        "num_visits": num_visits,
    }
    return render(request, "task_manager/index.html", context=context)


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


def redirect_back(request, fallback_url):
    """Redirect to the "next" URL of the form, if it's a safe local URL."""
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect(fallback_url)


@login_required
@require_POST
def toggle_task_assignment(request, pk):
    task = get_object_or_404(Task, pk=pk)
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
    task = get_object_or_404(Task, pk=pk)
    task.is_completed = not task.is_completed
    task.save(update_fields=["is_completed"])
    if task.is_completed:
        messages.success(request, f'"{task}" is completed. Nice work!')
    else:
        messages.info(request, f'"{task}" is open again.')
    return redirect_back(request, task.get_absolute_url())


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


class TeamListView(LoginRequiredMixin, SearchMixin, generic.ListView):
    model = Team
    paginate_by = 9

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                num_members=Count("members", distinct=True),
                num_projects=Count("projects", distinct=True),
            )
            .order_by("name")
            .prefetch_related("members", "projects")
        )


class TeamDetailView(LoginRequiredMixin, generic.DetailView):
    model = Team
    queryset = Team.objects.prefetch_related(
        "members__position", "projects"
    )


class TeamCreateView(
    LoginRequiredMixin, ObjectMessageMixin, generic.CreateView
):
    model = Team
    form_class = TeamForm
    success_message = 'Team "%(object)s" was created.'


class TeamUpdateView(
    LoginRequiredMixin, ObjectMessageMixin, generic.UpdateView
):
    model = Team
    form_class = TeamForm
    success_message = 'Team "%(object)s" was updated.'


class TeamDeleteView(
    LoginRequiredMixin, ConfirmDeleteMixin, generic.DeleteView
):
    model = Team
    success_url = reverse_lazy("task_manager:team-list")


@login_required
@require_POST
def toggle_team_membership(request, pk):
    team = get_object_or_404(Team, pk=pk)
    if team.members.filter(pk=request.user.pk).exists():
        team.members.remove(request.user)
        messages.info(request, f'You left the team "{team}".')
    else:
        team.members.add(request.user)
        messages.success(request, f'You joined the team "{team}".')
    return redirect_back(request, team.get_absolute_url())


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
