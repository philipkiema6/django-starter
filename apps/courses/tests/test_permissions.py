from django.urls import reverse

from apps.courses.models import Course
from apps.users.models import CustomUser

from .base import CoursesTestBase


class InstructorPermissionsTest(CoursesTestBase):
    def setUp(self):
        self.course = Course.objects.create(instructor=self.instructor, title="Owned Course")

    def test_student_cannot_access_instructor_views(self):
        response = self.student_client.get(reverse("courses:instructor_course_list"))
        self.assertEqual(response.status_code, 403)

    def test_instructor_can_access_own_course(self):
        response = self.instructor_client.get(reverse("courses:instructor_course_detail", args=[self.course.slug]))
        self.assertEqual(response.status_code, 200)

    def test_another_instructor_cannot_access_someone_elses_course(self):
        other_instructor = CustomUser.objects.create_user(
            username="other@example.com", email="other@example.com", password="password123"
        )
        other_instructor.profile.role = other_instructor.profile.ROLE_INSTRUCTOR
        other_instructor.profile.save()
        other_client = self.client_class()
        other_client.force_login(other_instructor)

        response = other_client.get(reverse("courses:instructor_course_detail", args=[self.course.slug]))
        self.assertEqual(response.status_code, 404)

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse("courses:instructor_course_list"))
        self.assertRedirects(response, f"/accounts/login/?next={reverse('courses:instructor_course_list')}")
