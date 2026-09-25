from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase
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


class WorkerModelTests(TestCase):
    def test_str_includes_full_name(self):
        worker = Worker.objects.create_user(
            username="taras", first_name="Taras", last_name="Melnyk"
        )
        self.assertEqual(str(worker), "taras (Taras Melnyk)")

    def test_str_without_full_name_is_username(self):
        worker = Worker.objects.create_user(username="taras")
        self.assertEqual(str(worker), "taras")

    def test_initials_are_taken_from_full_name(self):
        worker = Worker.objects.create_user(
            username="taras", first_name="taras", last_name="melnyk"
        )
        self.assertEqual(worker.initials, "TM")

    def test_initials_fall_back_to_username(self):
        worker = Worker.objects.create_user(username="taras")
        self.assertEqual(worker.initials, "TA")

    def test_deleting_position_keeps_its_workers(self):
        position = Position.objects.create(name="Developer")
        worker = Worker.objects.create_user(
            username="taras", position=position
        )

        position.delete()

        worker.refresh_from_db()
        self.assertIsNone(worker.position)


class TagModelTests(TestCase):
    def test_kebab_case_name_is_valid(self):
        Tag(name="landing-page-layout").full_clean()

    def test_name_that_is_not_kebab_case_is_rejected(self):
        for name in ("Landing Page", "python_refactoring", "-auth", "a--b"):
            with self.subTest(name=name):
                with self.assertRaises(ValidationError):
                    Tag(name=name).full_clean()


class ProjectModelTests(TestCase):
    def test_get_members_returns_unique_workers_of_all_teams(self):
        taras = Worker.objects.create_user(username="taras")
        iryna = Worker.objects.create_user(username="iryna")
        backend = Team.objects.create(name="Backend")
        backend.members.add(taras, iryna)
        quality = Team.objects.create(name="Quality")
        quality.members.add(iryna)
        project = Project.objects.create(name="Payments API")
        project.teams.add(backend, quality)

        self.assertCountEqual(project.get_members(), [taras, iryna])


class TaskModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.task_type = TaskType.objects.create(name="Bug")
        cls.project = Project.objects.create(name="Customer portal")

    def create_task(self, **fields):
        defaults = {
            "name": "Fix login redirect",
            "deadline": timezone.localdate(),
            "task_type": self.task_type,
            "project": self.project,
        }
        return Task.objects.create(**(defaults | fields))

    def test_default_priority_is_medium(self):
        self.assertEqual(self.create_task().priority, Task.Priority.MEDIUM)

    def test_open_task_with_past_deadline_is_overdue(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        self.assertTrue(self.create_task(deadline=yesterday).is_overdue)

    def test_task_due_today_is_not_overdue(self):
        self.assertFalse(self.create_task().is_overdue)

    def test_completed_task_is_never_overdue(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        task = self.create_task(deadline=yesterday, is_completed=True)
        self.assertFalse(task.is_overdue)

    def test_task_type_in_use_cannot_be_deleted(self):
        self.create_task()
        with self.assertRaises(ProtectedError):
            self.task_type.delete()

    def test_deleting_project_deletes_its_tasks(self):
        self.create_task()
        self.project.delete()
        self.assertFalse(Task.objects.exists())
