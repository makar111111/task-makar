from django.test import SimpleTestCase

from task_manager.models import Worker
from task_manager.templatetags.task_manager_extras import avatar_class


class AvatarClassFilterTests(SimpleTestCase):
    def test_avatar_color_depends_on_worker_id(self):
        self.assertEqual(avatar_class(Worker(pk=7)), "tm-av-2")
        self.assertEqual(avatar_class(Worker(pk=10)), "tm-av-0")
