from django.test import TestCase
from django.urls import reverse

from task_manager.models import Project, Team
from task_manager.tests.utils import create_worker

TEAM_LIST_URL = reverse("task_manager:team-list")


class TeamListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_worker()
        cls.core = Team.objects.create(name="Core platform")
        cls.growth = Team.objects.create(name="Growth")
        cls.core.members.add(cls.user, create_worker("iryna"))
        Project.objects.create(name="Payments API").teams.add(cls.core)

    def setUp(self):
        self.client.force_login(self.user)

    def test_login_is_required(self):
        self.client.logout()
        self.assertEqual(self.client.get(TEAM_LIST_URL).status_code, 302)

    def test_search_by_name(self):
        response = self.client.get(TEAM_LIST_URL, {"search": "grow"})
        self.assertEqual(list(response.context["team_list"]), [self.growth])

    def test_counts_members_and_projects(self):
        response = self.client.get(TEAM_LIST_URL, {"search": "core"})
        team = response.context["team_list"][0]
        self.assertEqual(team.num_members, 2)
        self.assertEqual(team.num_projects, 1)


class TeamMembershipTests(TestCase):
    def test_join_and_leave_team(self):
        user = create_worker()
        team = Team.objects.create(name="Quality")
        url = reverse("task_manager:team-toggle-membership", args=[team.pk])
        self.client.force_login(user)

        self.client.post(url)
        self.assertIn(user, team.members.all())

        self.client.post(url)
        self.assertNotIn(user, team.members.all())

    def test_membership_accepts_only_post(self):
        team = Team.objects.create(name="Quality")
        url = reverse("task_manager:team-toggle-membership", args=[team.pk])
        self.client.force_login(create_worker())
        self.assertEqual(self.client.get(url).status_code, 405)


class TeamCreateUpdateDeleteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_worker()

    def setUp(self):
        self.client.force_login(self.user)

    def test_create_team_with_members(self):
        response = self.client.post(
            reverse("task_manager:team-create"),
            {"name": "Quality", "members": [self.user.pk]},
        )
        team = Team.objects.get(name="Quality")
        self.assertRedirects(response, team.get_absolute_url())
        self.assertEqual(list(team.members.all()), [self.user])

    def test_team_name_must_be_unique(self):
        Team.objects.create(name="Quality")
        response = self.client.post(
            reverse("task_manager:team-create"), {"name": "Quality"}
        )
        self.assertIn("name", response.context["form"].errors)

    def test_update_team(self):
        team = Team.objects.create(name="Old name")
        url = reverse("task_manager:team-update", args=[team.pk])
        self.client.post(url, {"name": "New name"})
        team.refresh_from_db()
        self.assertEqual(team.name, "New name")

    def test_delete_team(self):
        team = Team.objects.create(name="Quality")
        url = reverse("task_manager:team-delete", args=[team.pk])
        response = self.client.post(url)
        self.assertRedirects(response, TEAM_LIST_URL)
        self.assertFalse(Team.objects.exists())
