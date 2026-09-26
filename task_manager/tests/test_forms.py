from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from task_manager.forms import TaskForm
from task_manager.models import Project, TaskType
from task_manager.tests.utils import create_task


class TaskFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.task_type = TaskType.objects.create(name="Bug")
        cls.project = Project.objects.create(name="Customer portal")

    def make_form(self, deadline, instance=None):
        return TaskForm(
            data={
                "name": "Fix login redirect",
                "project": self.project.pk,
                "task_type": self.task_type.pk,
                "priority": "high",
                "deadline": deadline,
            },
            instance=instance,
        )

    def test_deadline_today_is_valid(self):
        self.assertTrue(self.make_form(timezone.localdate()).is_valid())

    def test_deadline_in_the_past_is_invalid(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        form = self.make_form(yesterday)
        self.assertFalse(form.is_valid())
        self.assertIn("deadline", form.errors)

    def test_overdue_task_can_be_saved_with_its_old_deadline(self):
        task = create_task(due_in_days=-3)
        form = self.make_form(task.deadline, instance=task)
        self.assertTrue(form.is_valid())

    def test_overdue_task_cannot_get_another_past_deadline(self):
        task = create_task(due_in_days=-3)
        form = self.make_form(task.deadline - timedelta(days=1), task)
        self.assertFalse(form.is_valid())
