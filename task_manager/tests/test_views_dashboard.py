from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from task_manager.tests.utils import create_task, create_worker

INDEX_URL = reverse("task_manager:index")


class DashboardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_worker(first_name="Taras")
        cls.my_overdue_task = create_task("Overdue task", due_in_days=-1)
        cls.my_overdue_task.assignees.add(cls.user)
        create_task("Upcoming task", due_in_days=5)
        done_task = create_task("Done task", is_completed=True)
        done_task.assignees.add(cls.user)

    def setUp(self):
        self.client.force_login(self.user)

    def test_login_is_required(self):
        self.client.logout()
        response = self.client.get(INDEX_URL)
        self.assertRedirects(
            response,
            f"{settings.LOGIN_URL}?next={INDEX_URL}",
            fetch_redirect_response=False,
        )

    def test_counts_open_completed_and_overdue_tasks(self):
        response = self.client.get(INDEX_URL)
        self.assertEqual(response.context["num_open"], 2)
        self.assertEqual(response.context["num_completed"], 1)
        self.assertEqual(response.context["num_overdue"], 1)
        self.assertEqual(response.context["completed_percent"], 33)

    def test_shows_only_open_tasks_of_the_user(self):
        response = self.client.get(INDEX_URL)
        self.assertEqual(
            list(response.context["my_tasks"]), [self.my_overdue_task]
        )
        self.assertContains(response, "1 of them is overdue")

    def test_counts_visits_in_session(self):
        self.client.get(INDEX_URL)
        response = self.client.get(INDEX_URL)
        self.assertEqual(response.context["num_visits"], 2)
        self.assertContains(response, "This is your 2nd visit")
