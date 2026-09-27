from django.test import TestCase
from django.urls import reverse

from task_manager.models import Position, Worker


class AdminSiteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = Worker.objects.create_superuser(
            username="admin", password="admin-pass-123"
        )
        cls.worker = Worker.objects.create_user(
            username="taras",
            password="taras-pass-123",
            position=Position.objects.create(name="Developer"),
        )

    def setUp(self):
        self.client.force_login(self.admin_user)

    def test_worker_list_shows_position(self):
        url = reverse("admin:task_manager_worker_changelist")
        self.assertContains(self.client.get(url), "Developer")

    def test_worker_change_page_has_position_field(self):
        url = reverse(
            "admin:task_manager_worker_change", args=[self.worker.pk]
        )
        self.assertContains(self.client.get(url), 'name="position"')

    def test_worker_add_page_has_additional_info_fields(self):
        response = self.client.get(reverse("admin:task_manager_worker_add"))
        for field in ("first_name", "last_name", "email", "position"):
            with self.subTest(field=field):
                self.assertContains(response, f'name="{field}"')

    def test_changelist_of_every_model_opens(self):
        models = ("position", "project", "tag", "task", "tasktype", "team")
        for model in models:
            with self.subTest(model=model):
                url = reverse(f"admin:task_manager_{model}_changelist")
                self.assertEqual(self.client.get(url).status_code, 200)
