from apps.courses.models import Course

from .base import CoursesTestBase


class CourseSlugTest(CoursesTestBase):
    def test_slug_auto_generated_from_title(self):
        course = Course.objects.create(instructor=self.instructor, title="Intro to Django")
        self.assertEqual(course.slug, "intro-to-django")

    def test_slug_deduplicates_on_collision(self):
        Course.objects.create(instructor=self.instructor, title="Intro to Django")
        second = Course.objects.create(instructor=self.instructor, title="Intro to Django")
        self.assertEqual(second.slug, "intro-to-django-2")

    def test_explicit_slug_is_preserved(self):
        course = Course.objects.create(instructor=self.instructor, title="Intro to Django", slug="custom-slug")
        self.assertEqual(course.slug, "custom-slug")
