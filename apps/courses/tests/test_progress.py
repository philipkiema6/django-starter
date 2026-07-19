from django.urls import reverse

from apps.courses.models import Course, Enrollment, Lesson, LessonProgress

from .base import CoursesTestBase


class ProgressTest(CoursesTestBase):
    def setUp(self):
        self.course = Course.objects.create(instructor=self.instructor, title="Django Basics", is_published=True)
        self.lesson1 = Lesson.objects.create(course=self.course, title="Lesson 1", order=0)
        self.lesson2 = Lesson.objects.create(course=self.course, title="Lesson 2", order=1)
        self.enrollment = Enrollment.objects.create(student=self.student, course=self.course)

    def test_progress_percent_zero_with_no_completions(self):
        self.assertEqual(self.enrollment.progress_percent, 0)

    def test_progress_percent_zero_lessons_does_not_divide_by_zero(self):
        empty_course = Course.objects.create(instructor=self.instructor, title="Empty", is_published=True)
        enrollment = Enrollment.objects.create(student=self.student, course=empty_course)
        self.assertEqual(enrollment.progress_percent, 0)

    def test_mark_lesson_complete_creates_progress(self):
        response = self.student_client.post(reverse("courses:mark_complete", args=[self.course.slug, self.lesson1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            LessonProgress.objects.filter(
                enrollment=self.enrollment, lesson=self.lesson1, completed_at__isnull=False
            ).exists()
        )
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.progress_percent, 50)

    def test_mark_lesson_complete_is_idempotent(self):
        url = reverse("courses:mark_complete", args=[self.course.slug, self.lesson1.id])
        self.student_client.post(url)
        self.student_client.post(url)
        self.assertEqual(LessonProgress.objects.filter(enrollment=self.enrollment, lesson=self.lesson1).count(), 1)

    def test_full_completion_is_100_percent(self):
        self.student_client.post(reverse("courses:mark_complete", args=[self.course.slug, self.lesson1.id]))
        self.student_client.post(reverse("courses:mark_complete", args=[self.course.slug, self.lesson2.id]))
        self.enrollment.refresh_from_db()
        self.assertEqual(self.enrollment.progress_percent, 100)
        self.assertTrue(self.enrollment.is_complete)
