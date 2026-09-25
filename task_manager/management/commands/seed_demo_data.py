import json
from datetime import timedelta
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from task_manager.models import (
    Position,
    Project,
    Tag,
    Task,
    TaskType,
    Team,
    Worker,
)

DEMO_DATA_FILE = Path(__file__).resolve().parent.parent / "demo_data.json"
DEMO_PASSWORD = "demo12345"


class Command(BaseCommand):
    help = (  # noqa: VNE003 (Django reads the "help" attribute)
        "Fill the database with demo workers, teams, projects and tasks. "
        "Deadlines are counted from today. Safe to run several times: "
        "existing records are kept as they are."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        demo = json.loads(DEMO_DATA_FILE.read_text(encoding="utf-8"))

        positions = self.create_named(Position, demo["positions"])
        task_types = self.create_named(TaskType, demo["task_types"])
        tags = self.create_named(Tag, demo["tags"])
        workers = self.create_workers(demo["workers"], positions)
        teams = self.create_teams(demo["teams"], workers)
        projects = self.create_projects(demo["projects"], teams)
        self.create_tasks(demo["tasks"], projects, task_types, tags, workers)

        self.stdout.write(
            self.style.SUCCESS(
                'Demo data is ready. Log in as "demo" '
                f'with password "{DEMO_PASSWORD}".'
            )
        )

    @staticmethod
    def create_named(model, names):
        return {
            name: model.objects.get_or_create(name=name)[0] for name in names
        }

    @staticmethod
    def create_workers(worker_specs, positions):
        workers = {}
        for spec in worker_specs:
            username = spec["username"]
            worker, created = Worker.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": spec["first_name"],
                    "last_name": spec["last_name"],
                    "email": f"{username}@example.com",
                    "position": positions[spec["position"]],
                },
            )
            if created:
                worker.set_password(DEMO_PASSWORD)
                worker.save(update_fields=["password"])
            workers[username] = worker
        return workers

    @staticmethod
    def create_teams(team_specs, workers):
        teams = {}
        for spec in team_specs:
            team, _ = Team.objects.get_or_create(name=spec["name"])
            team.members.add(*(workers[name] for name in spec["members"]))
            teams[team.name] = team
        return teams

    @staticmethod
    def create_projects(project_specs, teams):
        projects = {}
        for spec in project_specs:
            project, _ = Project.objects.get_or_create(
                name=spec["name"],
                defaults={"description": spec["description"]},
            )
            project.teams.add(*(teams[name] for name in spec["teams"]))
            projects[project.name] = project
        return projects

    @staticmethod
    def create_tasks(task_specs, projects, task_types, tags, workers):
        today = timezone.localdate()
        for spec in task_specs:
            task, created = Task.objects.get_or_create(
                name=spec["name"],
                project=projects[spec["project"]],
                defaults={
                    "description": spec["description"],
                    "task_type": task_types[spec["task_type"]],
                    "priority": spec["priority"],
                    "deadline": today + timedelta(days=spec["due_in_days"]),
                    "is_completed": spec["is_completed"],
                },
            )
            if created:
                task.assignees.set(workers[name] for name in spec["assignees"])
                task.tags.set(tags[name] for name in spec["tags"])
