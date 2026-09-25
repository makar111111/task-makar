from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from task_manager.management.commands.seed_demo_data import DEMO_PASSWORD
from task_manager.models import Project, Task, Team, Worker


class SeedDemoDataCommandTests(TestCase):
    def seed(self):
        call_command("seed_demo_data", stdout=StringIO())

    def test_demo_user_can_log_in(self):
        self.seed()
        self.assertTrue(
            self.client.login(username="demo", password=DEMO_PASSWORD)
        )

    def test_demo_data_has_open_overdue_and_completed_tasks(self):
        self.seed()
        today = timezone.localdate()
        self.assertTrue(Task.objects.filter(is_completed=True).exists())
        open_tasks = Task.objects.filter(is_completed=False)
        self.assertTrue(open_tasks.filter(deadline__gte=today).exists())
        self.assertTrue(open_tasks.filter(deadline__lt=today).exists())

    def test_running_twice_does_not_duplicate_records(self):
        self.seed()
        counts = [model.objects.count() for model in (Worker, Team, Project)]
        tasks_count = Task.objects.count()

        self.seed()

        self.assertEqual(
            [model.objects.count() for model in (Worker, Team, Project)],
            counts,
        )
        self.assertEqual(Task.objects.count(), tasks_count)
