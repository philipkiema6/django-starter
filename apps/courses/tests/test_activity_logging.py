from django.urls import reverse

from apps.activity.models import ActivityLog
from apps.courses.models import Course

from .base import CoursesTestBase


class CourseActivityLoggingTest(CoursesTestBase):
    def test_creating_a_course_logs_activity(self):
        self.instructor_client.post(
            reverse("courses:instructor_course_create"),
            {"title": "New Course", "description": "", "is_published": False},
        )
        self.assertTrue(ActivityLog.objects.filter(action="course.created").exists())

    def test_publishing_a_course_logs_activity_once(self):
        course = Course.objects.create(instructor=self.instructor, title="Draft Course", is_published=False)
        url = reverse("courses:instructor_course_edit", args=[course.slug])

        self.instructor_client.post(url, {"title": course.title, "description": "", "is_published": True})
        self.assertEqual(ActivityLog.objects.filter(action="course.published").count(), 1)

        # editing again while already published shouldn't log a second "published" event
        self.instructor_client.post(url, {"title": course.title, "description": "updated", "is_published": True})
        self.assertEqual(ActivityLog.objects.filter(action="course.published").count(), 1)

    def test_enrolling_logs_activity(self):
        course = Course.objects.create(instructor=self.instructor, title="Enroll Me", is_published=True)
        self.student_client.post(reverse("courses:enroll", args=[course.slug]))
        self.assertTrue(ActivityLog.objects.filter(action="enrollment.created").exists())
