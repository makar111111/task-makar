from django.test import TestCase
from django.urls import reverse

from task_manager.models import Project, Task, Team
from task_manager.tests.utils import create_task, create_worker

PROJECT_LIST_URL = reverse("task_manager:project-list")


class ProjectListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_worker()
        cls.portal = Project.objects.create(name="Customer portal")
        cls.payments = Project.objects.create(name="Payments API")

    def setUp(self):
        self.client.force_login(self.user)

    def test_login_is_required(self):
        self.client.logout()
        self.assertEqual(self.client.get(PROJECT_LIST_URL).status_code, 302)

    def test_search_by_name(self):
        response = self.client.get(PROJECT_LIST_URL, {"search": "pay"})
        self.assertEqual(
            list(response.context["project_list"]), [self.payments]
        )

    def test_counts_tasks_of_each_project(self):
        create_task("Open", project=self.portal)
        create_task("Overdue", due_in_days=-2, project=self.portal)
        create_task("Done", is_completed=True, project=self.portal)

        response = self.client.get(PROJECT_LIST_URL, {"search": "portal"})

        project = response.context["project_list"][0]
        self.assertEqual(project.num_tasks, 3)
        self.assertEqual(project.num_completed_tasks, 1)
        self.assertEqual(project.num_overdue_tasks, 1)
        self.assertContains(response, "33%")


class ProjectDetailTests(TestCase):
    def test_shows_open_and_completed_tasks_and_add_task_link(self):
        user = create_worker()
        open_task = create_task("Open task")
        done_task = create_task("Done task", is_completed=True)
        project = open_task.project
        self.client.force_login(user)

        response = self.client.get(project.get_absolute_url())

        self.assertEqual(list(response.context["open_tasks"]), [open_task])
        self.assertEqual(
            list(response.context["completed_tasks"]), [done_task]
        )
        self.assertContains(response, f"?project={project.pk}")


class ProjectCreateUpdateDeleteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_worker()
        cls.team = Team.objects.create(name="Core platform")

    def setUp(self):
        self.client.force_login(self.user)

    def test_create_project_with_teams(self):
        response = self.client.post(
            reverse("task_manager:project-create"),
            {"name": "Mobile app", "teams": [self.team.pk]},
        )

        project = Project.objects.get(name="Mobile app")
        self.assertRedirects(response, project.get_absolute_url())
        self.assertEqual(list(project.teams.all()), [self.team])

    def test_update_project(self):
        project = Project.objects.create(name="Old name")
        url = reverse("task_manager:project-update", args=[project.pk])
        self.client.post(url, {"name": "New name", "description": "Text"})
        project.refresh_from_db()
        self.assertEqual(project.name, "New name")

    def test_delete_page_warns_about_tasks(self):
        project = create_task().project
        url = reverse("task_manager:project-delete", args=[project.pk])
        self.assertContains(self.client.get(url), "1 task of this project")

    def test_delete_project_with_its_tasks(self):
        project = create_task().project
        url = reverse("task_manager:project-delete", args=[project.pk])

        response = self.client.post(url)

        self.assertRedirects(response, PROJECT_LIST_URL)
        self.assertFalse(Project.objects.filter(pk=project.pk).exists())
        self.assertFalse(Task.objects.exists())
