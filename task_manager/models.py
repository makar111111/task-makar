from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class Position(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Worker(AbstractUser):
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workers",
    )

    class Meta:
        ordering = ["username"]
        verbose_name = "worker"
        verbose_name_plural = "workers"

    def __str__(self):
        full_name = self.get_full_name()
        return f"{self.username} ({full_name})" if full_name else self.username

    def get_absolute_url(self):
        return reverse("task_manager:worker-detail", kwargs={"pk": self.pk})

    @property
    def initials(self):
        """Two letters for the avatar: "Taras Melnyk" -> "TM"."""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.username[:2].upper()


class Team(models.Model):
    name = models.CharField(max_length=255, unique=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="teams",
        blank=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("task_manager:team-detail", kwargs={"pk": self.pk})


class Project(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    teams = models.ManyToManyField(Team, related_name="projects", blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("task_manager:project-detail", kwargs={"pk": self.pk})

    def get_members(self):
        """Unique workers from all teams of the project.

        Uses prefetched ``teams__members`` when available, so listing
        members of many projects doesn't cost a query per team.
        """
        members = {}
        for team in self.teams.all():
            for member in team.members.all():
                members[member.pk] = member
        return list(members.values())
