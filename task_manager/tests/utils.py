from datetime import timedelta

from django.utils import timezone

from task_manager.models import Project, Task, TaskType, Worker

TEST_PASSWORD = "test-pass-123"


def create_worker(username="taras", **fields):
    return Worker.objects.create_user(
        username=username, password=TEST_PASSWORD, **fields
    )


def create_task(name="Fix login redirect", due_in_days=3, **fields):
    """Create a task; the task type and the project are created if needed."""
    defaults = {
        "deadline": timezone.localdate() + timedelta(days=due_in_days),
        "task_type": TaskType.objects.get_or_create(name="Bug")[0],
        "project": Project.objects.get_or_create(name="Customer portal")[0],
    }
    return Task.objects.create(name=name, **(defaults | fields))
