from django.urls import reverse

from apps.activity.models import ActivityLog
from apps.courses.certificates import generate_certificate_pdf
from apps.courses.models import Course, Enrollment, Lesson, LessonProgress

from .base import CoursesTestBase


class CertificateTest(CoursesTestBase):
    def setUp(self):
        self.course = Course.objects.create(instructor=self.instructor, title="Django Basics", is_published=True)
        self.lesson = Lesson.objects.create(course=self.course, title="Only Lesson", order=0)
        self.enrollment = Enrollment.objects.create(student=self.student, course=self.course)

    def test_generate_certificate_pdf_returns_valid_pdf_bytes(self):
        pdf_bytes = generate_certificate_pdf(self.enrollment)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_certificate_download_blocked_before_completion(self):
        response = self.student_client.get(reverse("courses:certificate", args=[self.course.slug]))
        # fetch_redirect_response=False: courses:learn itself redirects again (to the first
        # lesson), so following the chain to a 200 isn't the thing being asserted here.
        self.assertRedirects(response, reverse("courses:learn", args=[self.course.slug]), fetch_redirect_response=False)

    def test_certificate_download_succeeds_after_completion(self):
        LessonProgress.objects.create(
            enrollment=self.enrollment, lesson=self.lesson, completed_at="2026-01-01T00:00:00Z"
        )
        response = self.student_client.get(reverse("courses:certificate", args=[self.course.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_certificate_download_requires_enrollment(self):
        other_student = self.instructor.__class__.objects.create_user(
            username="unenrolled@example.com", email="unenrolled@example.com", password="password123"
        )
        client = self.client_class()
        client.force_login(other_student)
        response = client.get(reverse("courses:certificate", args=[self.course.slug]))
        self.assertEqual(response.status_code, 404)

    def test_completion_logs_activity(self):
        self.student_client.post(reverse("courses:mark_complete", args=[self.course.slug, self.lesson.id]))
        self.assertTrue(ActivityLog.objects.filter(action="lesson.completed").exists())
        self.assertTrue(ActivityLog.objects.filter(action="course.completed").exists())

    def test_certificate_download_logs_activity(self):
        LessonProgress.objects.create(
            enrollment=self.enrollment, lesson=self.lesson, completed_at="2026-01-01T00:00:00Z"
        )
        self.student_client.get(reverse("courses:certificate", args=[self.course.slug]))
        self.assertTrue(ActivityLog.objects.filter(action="certificate.downloaded").exists())
