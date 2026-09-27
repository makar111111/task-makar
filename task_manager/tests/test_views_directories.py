from django.test import TestCase
from django.urls import reverse

from task_manager.models import Position, Tag, TaskType
from task_manager.tests.utils import create_task, create_worker


class DirectoryListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_worker()

    def setUp(self):
        self.client.force_login(self.user)

    def test_lists_require_login(self):
        self.client.logout()
        for name in ("position-list", "tasktype-list", "tag-list"):
            with self.subTest(name=name):
                response = self.client.get(reverse(f"task_manager:{name}"))
                self.assertEqual(response.status_code, 302)

    def test_search_by_name(self):
        Tag.objects.create(name="frontend")
        backend = Tag.objects.create(name="backend")
        response = self.client.get(
            reverse("task_manager:tag-list"), {"search": "back"}
        )
        self.assertEqual(list(response.context["object_list"]), [backend])

    def test_counts_related_objects(self):
        task = create_task()
        response = self.client.get(reverse("task_manager:tasktype-list"))
        task_type = response.context["object_list"][0]
        self.assertEqual(task_type, task.task_type)
        self.assertEqual(task_type.num_related, 1)
        self.assertContains(response, "1 task")


class DirectoryCreateUpdateDeleteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_worker()

    def setUp(self):
        self.client.force_login(self.user)

    def test_create_position(self):
        response = self.client.post(
            reverse("task_manager:position-create"), {"name": "DevOps"}
        )
        self.assertRedirects(response, reverse("task_manager:position-list"))
        self.assertTrue(Position.objects.filter(name="DevOps").exists())

    def test_tag_name_must_be_kebab_case(self):
        response = self.client.post(
            reverse("task_manager:tag-create"), {"name": "Landing Page"}
        )
        self.assertIn("name", response.context["form"].errors)
        self.assertFalse(Tag.objects.exists())

    def test_update_task_type(self):
        task_type = TaskType.objects.create(name="Bug")
        url = reverse("task_manager:tasktype-update", args=[task_type.pk])
        self.client.post(url, {"name": "Defect"})
        task_type.refresh_from_db()
        self.assertEqual(task_type.name, "Defect")

    def test_task_type_in_use_is_not_deleted(self):
        task_type = create_task().task_type
        url = reverse("task_manager:tasktype-delete", args=[task_type.pk])

        response = self.client.post(url, follow=True)

        self.assertTrue(TaskType.objects.filter(pk=task_type.pk).exists())
        self.assertContains(response, "cannot be deleted")

    def test_delete_page_warns_that_task_type_is_in_use(self):
        task_type = create_task().task_type
        url = reverse("task_manager:tasktype-delete", args=[task_type.pk])
        response = self.client.get(url)
        self.assertContains(response, "Change their type first")
        self.assertNotContains(response, "Yes, delete")

    def test_deleting_position_keeps_workers(self):
        position = Position.objects.create(name="QA")
        worker = create_worker("iryna", position=position)
        url = reverse("task_manager:position-delete", args=[position.pk])

        self.client.post(url)

        worker.refresh_from_db()
        self.assertIsNone(worker.position)

    def test_delete_tag(self):
        tag = Tag.objects.create(name="auth")
        url = reverse("task_manager:tag-delete", args=[tag.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse("task_manager:tag-list"))
        self.assertFalse(Tag.objects.exists())
