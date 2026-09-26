from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from task_manager.models import Tag, Task
from task_manager.tests.utils import create_task, create_worker

TASK_LIST_URL = reverse("task_manager:task-list")


class TaskListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_worker()
        cls.login_task = create_task(
            "Fix login redirect", priority=Task.Priority.URGENT
        )
        cls.docs_task = create_task(
            "Write API docs", priority=Task.Priority.LOW
        )
        cls.done_task = create_task("Set up CI", is_completed=True)

    def setUp(self):
        self.client.force_login(self.user)

    def get_tasks(self, **params):
        response = self.client.get(TASK_LIST_URL, params)
        return list(response.context["task_list"])

    def test_login_is_required(self):
        self.client.logout()
        response = self.client.get(TASK_LIST_URL)
        self.assertRedirects(
            response, f"{reverse('login')}?next={TASK_LIST_URL}"
        )

    def test_shows_open_tasks_by_default(self):
        self.assertCountEqual(
            self.get_tasks(), [self.login_task, self.docs_task]
        )

    def test_filters_by_status(self):
        self.assertEqual(self.get_tasks(status="completed"), [self.done_task])
        self.assertEqual(len(self.get_tasks(status="all")), 3)

    def test_search_by_name_ignores_case(self):
        self.assertEqual(self.get_tasks(search="LOGIN"), [self.login_task])

    def test_filters_by_priority(self):
        self.assertEqual(self.get_tasks(priority="low"), [self.docs_task])

    def test_filters_by_tag(self):
        tag = Tag.objects.create(name="auth")
        self.login_task.tags.add(tag)
        self.assertEqual(self.get_tasks(tag=tag.pk), [self.login_task])

    def test_filters_by_assignee(self):
        self.login_task.assignees.add(self.user)
        self.assertEqual(
            self.get_tasks(assignee=self.user.pk), [self.login_task]
        )

    def test_invalid_filter_is_ignored(self):
        self.assertCountEqual(
            self.get_tasks(priority="someday"),
            [self.login_task, self.docs_task],
        )

    def test_pagination_links_keep_filters(self):
        for number in range(11):
            create_task(f"Bug number {number}")

        response = self.client.get(TASK_LIST_URL, {"search": "bug"})

        self.assertContains(response, "?search=bug&amp;page=2")


class TaskDetailTests(TestCase):
    def test_shows_task_details(self):
        worker = create_worker(first_name="Iryna", last_name="Bondar")
        task = create_task(description="Users land on a blank page.")
        task.assignees.add(worker)
        self.client.force_login(worker)

        response = self.client.get(task.get_absolute_url())

        self.assertContains(response, task.name)
        self.assertContains(response, "Users land on a blank page.")
        self.assertContains(response, "Customer portal")
        self.assertContains(response, "Iryna Bondar")


class TaskCreateUpdateDeleteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_worker()
        cls.task = create_task()

    def setUp(self):
        self.client.force_login(self.user)

    def get_form_data(self, **fields):
        form_data = {
            "name": "Add sign-in with Google",
            "project": self.task.project.pk,
            "task_type": self.task.task_type.pk,
            "priority": "high",
            "deadline": timezone.localdate().isoformat(),
            "assignees": [self.user.pk],
        }
        return form_data | fields

    def test_create_task(self):
        response = self.client.post(
            reverse("task_manager:task-create"), self.get_form_data()
        )

        task = Task.objects.get(name="Add sign-in with Google")
        self.assertRedirects(response, task.get_absolute_url())
        self.assertEqual(list(task.assignees.all()), [self.user])

    def test_create_page_preselects_project_from_query(self):
        response = self.client.get(
            reverse("task_manager:task-create"),
            {"project": self.task.project.pk},
        )
        self.assertEqual(
            response.context["form"].initial["project"],
            str(self.task.project.pk),
        )

    def test_task_with_past_deadline_is_not_created(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        response = self.client.post(
            reverse("task_manager:task-create"),
            self.get_form_data(deadline=yesterday.isoformat()),
        )
        self.assertContains(response, "The deadline can")
        self.assertFalse(
            Task.objects.filter(name="Add sign-in with Google").exists()
        )

    def test_update_task(self):
        url = reverse("task_manager:task-update", args=[self.task.pk])
        self.client.post(url, self.get_form_data(name="Renamed task"))
        self.task.refresh_from_db()
        self.assertEqual(self.task.name, "Renamed task")

    def test_delete_task(self):
        url = reverse("task_manager:task-delete", args=[self.task.pk])
        response = self.client.post(url)
        self.assertRedirects(response, TASK_LIST_URL)
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())
