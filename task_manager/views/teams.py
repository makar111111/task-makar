from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import generic
from django.views.decorators.http import require_POST

from task_manager.forms import TeamForm
from task_manager.models import Team
from task_manager.views.mixins import (
    ConfirmDeleteMixin,
    ObjectMessageMixin,
    SearchMixin,
    redirect_back,
)


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
