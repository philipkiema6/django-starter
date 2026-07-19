from django.test import Client, TestCase

from apps.users.models import CustomUser


class CoursesTestBase(TestCase):
    """Sets up one instructor and one student, each with a logged-in client."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.instructor = CustomUser.objects.create_user(
            username="instructor@example.com", email="instructor@example.com", password="password123"
        )
        cls.instructor.profile.role = cls.instructor.profile.ROLE_INSTRUCTOR
        cls.instructor.profile.save()

        cls.student = CustomUser.objects.create_user(
            username="student@example.com", email="student@example.com", password="password123"
        )

        cls.instructor_client = Client()
        cls.instructor_client.force_login(cls.instructor)
        cls.student_client = Client()
        cls.student_client.force_login(cls.student)
