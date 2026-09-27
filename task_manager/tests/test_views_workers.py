from django.test import TestCase
from django.urls import reverse

from task_manager.models import Position, Worker
from task_manager.tests.utils import create_task, create_worker

WORKER_LIST_URL = reverse("task_manager:worker-list")


class WorkerListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_worker(first_name="Taras", last_name="Melnyk")
        cls.iryna = create_worker(
            "iryna.b", first_name="Iryna", last_name="Bondar"
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_login_is_required(self):
        self.client.logout()
        response = self.client.get(WORKER_LIST_URL)
        self.assertEqual(response.status_code, 302)

    def test_search_by_first_name(self):
        response = self.client.get(WORKER_LIST_URL, {"search": "iryna"})
        self.assertEqual(list(response.context["worker_list"]), [self.iryna])

    def test_search_by_username(self):
        response = self.client.get(WORKER_LIST_URL, {"search": "iryna.b"})
        self.assertEqual(list(response.context["worker_list"]), [self.iryna])

    def test_counts_open_and_completed_tasks(self):
        create_task("Open task").assignees.add(self.iryna)
        create_task("Done task", is_completed=True).assignees.add(self.iryna)

        response = self.client.get(WORKER_LIST_URL, {"search": "iryna"})

        worker = response.context["worker_list"][0]
        self.assertEqual(worker.num_open_tasks, 1)
        self.assertEqual(worker.num_completed_tasks, 1)


class WorkerDetailTests(TestCase):
    def test_splits_open_and_completed_tasks(self):
        worker = create_worker()
        open_task = create_task("Open task")
        done_task = create_task("Done task", is_completed=True)
        worker.tasks.add(open_task, done_task)
        self.client.force_login(worker)

        response = self.client.get(worker.get_absolute_url())

        self.assertEqual(list(response.context["open_tasks"]), [open_task])
        self.assertEqual(
            list(response.context["completed_tasks"]), [done_task]
        )


class WorkerCreateUpdateDeleteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_worker()
        cls.position = Position.objects.create(name="QA")

    def setUp(self):
        self.client.force_login(self.user)

    def test_create_worker(self):
        response = self.client.post(
            reverse("task_manager:worker-create"),
            {
                "username": "iryna.b",
                "password1": "Strong-pass-2026",
                "password2": "Strong-pass-2026",
                "first_name": "Iryna",
                "last_name": "Bondar",
                "email": "iryna@example.com",
                "position": self.position.pk,
            },
        )

        worker = Worker.objects.get(username="iryna.b")
        self.assertRedirects(response, worker.get_absolute_url())
        self.assertEqual(worker.position, self.position)
        self.assertTrue(worker.check_password("Strong-pass-2026"))

    def test_name_and_email_are_required(self):
        response = self.client.post(
            reverse("task_manager:worker-create"),
            {
                "username": "iryna.b",
                "password1": "Strong-pass-2026",
                "password2": "Strong-pass-2026",
            },
        )
        form = response.context["form"]
        for field in ("first_name", "last_name", "email"):
            with self.subTest(field=field):
                self.assertIn(field, form.errors)

    def test_update_worker_position(self):
        url = reverse("task_manager:worker-update", args=[self.user.pk])
        self.client.post(
            url,
            {
                "first_name": "Taras",
                "last_name": "Melnyk",
                "email": "taras@example.com",
                "position": self.position.pk,
            },
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.position, self.position)

    def test_delete_worker(self):
        other = create_worker("other")
        url = reverse("task_manager:worker-delete", args=[other.pk])
        response = self.client.post(url)
        self.assertRedirects(response, WORKER_LIST_URL)
        self.assertFalse(Worker.objects.filter(pk=other.pk).exists())

    def test_deleting_own_account_shows_warning(self):
        url = reverse("task_manager:worker-delete", args=[self.user.pk])
        self.assertContains(self.client.get(url), "your own account")
