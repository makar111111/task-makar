from django.conf import settings
from django.contrib.auth import views as auth_views

from task_manager.demo import DEMO_PASSWORD, DEMO_USERNAME


class LoginView(auth_views.LoginView):
    """Login page that shows the demo account when DEMO_MODE is on."""

    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if settings.DEMO_MODE:
            context["demo_credentials"] = {
                "username": DEMO_USERNAME,
                "password": DEMO_PASSWORD,
            }
        return context
