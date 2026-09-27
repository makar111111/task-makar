from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

validate_kebab_case = RegexValidator(
    regex=r"^[a-z0-9]+(-[a-z0-9]+)*$",
    message=(
        "Use kebab-case: lowercase letters and digits separated by "
        "single hyphens, e.g. landing-page-layout."
    ),
)


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


class TaskType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(
        max_length=50,
        unique=True,
        validators=[validate_kebab_case],
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Task(models.Model):
    class Priority(models.TextChoices):
        URGENT = "urgent", "Urgent"
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    deadline = models.DateField()
    is_completed = models.BooleanField(default=False)
    priority = models.CharField(
        max_length=10,
        choices=Priority,
        default=Priority.MEDIUM,
    )
    task_type = models.ForeignKey(
        TaskType,
        on_delete=models.PROTECT,
        related_name="tasks",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
    )
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="tasks",
        blank=True,
    )
    tags = models.ManyToManyField(Tag, related_name="tasks", blank=True)

    class Meta:
        ordering = ["is_completed", "deadline", "name"]
        indexes = [
            # Task lists are sorted by status and deadline, and overdue
            # tasks are open tasks with a past deadline. The project needs
            # no index here: Django adds one to every ForeignKey.
            models.Index(
                fields=["is_completed", "deadline"],
                name="task_status_deadline_idx",
            ),
            models.Index(fields=["priority"], name="task_priority_idx"),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("task_manager:task-detail", kwargs={"pk": self.pk})

    @property
    def is_overdue(self):
        return not self.is_completed and self.deadline < timezone.localdate()
