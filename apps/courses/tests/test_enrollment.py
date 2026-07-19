from django.urls import reverse

from apps.courses.models import Course, Enrollment

from .base import CoursesTestBase


class EnrollmentTest(CoursesTestBase):
    def setUp(self):
        self.course = Course.objects.create(instructor=self.instructor, title="Django Basics", is_published=True)

    def test_student_can_enroll(self):
        response = self.student_client.post(reverse("courses:enroll", args=[self.course.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=self.course).exists())

    def test_enroll_is_idempotent(self):
        self.student_client.post(reverse("courses:enroll", args=[self.course.slug]))
        self.student_client.post(reverse("courses:enroll", args=[self.course.slug]))
        self.assertEqual(Enrollment.objects.filter(student=self.student, course=self.course).count(), 1)

    def test_instructor_cannot_self_enroll(self):
        response = self.instructor_client.post(reverse("courses:enroll", args=[self.course.slug]))
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Enrollment.objects.filter(student=self.instructor, course=self.course).exists())
