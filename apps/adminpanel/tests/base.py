from django.test import Client, TestCase

from apps.users.models import CustomUser


class AdminPanelTestBase(TestCase):
    """One staff (superuser) account and one ordinary student, each with a logged-in client."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.staff = CustomUser.objects.create_superuser(
            username="staff@example.com", email="staff@example.com", password="password123"
        )
        cls.student = CustomUser.objects.create_user(
            username="student@example.com", email="student@example.com", password="password123"
        )

        cls.staff_client = Client()
        cls.staff_client.force_login(cls.staff)
        cls.student_client = Client()
        cls.student_client.force_login(cls.student)
