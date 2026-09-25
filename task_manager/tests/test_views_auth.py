from django.test import TestCase, override_settings
from django.urls import reverse

from task_manager.demo import DEMO_PASSWORD
from task_manager.tests.utils import TEST_PASSWORD, create_worker

LOGIN_URL = reverse("login")
LOGOUT_URL = reverse("logout")
INDEX_URL = reverse("task_manager:index")


class LoginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = create_worker()

    def test_login_page_opens(self):
        response = self.client.get(LOGIN_URL)
        self.assertContains(response, "Welcome back")

    def test_valid_credentials_open_dashboard(self):
        response = self.client.post(
            LOGIN_URL, {"username": "taras", "password": TEST_PASSWORD}
        )
        self.assertRedirects(response, INDEX_URL)

    def test_wrong_password_shows_error(self):
        response = self.client.post(
            LOGIN_URL, {"username": "taras", "password": "wrong"}
        )
        self.assertContains(response, "Please enter a correct username")

    def test_signed_in_user_is_redirected_to_dashboard(self):
        self.client.force_login(self.user)
        self.assertRedirects(self.client.get(LOGIN_URL), INDEX_URL)

    @override_settings(DEMO_MODE=True)
    def test_demo_credentials_are_shown_in_demo_mode(self):
        self.assertContains(self.client.get(LOGIN_URL), DEMO_PASSWORD)

    @override_settings(DEMO_MODE=False)
    def test_demo_credentials_are_hidden_by_default(self):
        self.assertNotContains(self.client.get(LOGIN_URL), DEMO_PASSWORD)


class LogoutTests(TestCase):
    def test_logout_signs_user_out(self):
        self.client.force_login(create_worker())

        response = self.client.post(LOGOUT_URL)

        self.assertContains(response, "You're signed out")
        self.assertNotIn("_auth_user_id", self.client.session)
