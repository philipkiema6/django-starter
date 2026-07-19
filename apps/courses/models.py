import uuid

from django.db import models
from django.utils.text import slugify

from apps.users.models import CustomUser
from apps.utils.models import BaseModel


def _course_cover_filename(instance, filename):
    """Use a random filename to prevent overwriting existing files & to fix caching issues."""
    return f"course-covers/{uuid.uuid4()}.{filename.split('.')[-1]}"


class Course(BaseModel):
    instructor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="courses_taught")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to=_course_cover_filename, blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self) -> str:
        base_slug = slugify(self.title) or "course"
        slug = base_slug
        suffix = 1
        while Course.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            suffix += 1
            slug = f"{base_slug}-{suffix}"
        return slug

    @property
    def student_count(self) -> int:
        return self.enrollments.count()


class Lesson(BaseModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return f"{self.course.title} — {self.title}"


class Enrollment(BaseModel):
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")

    class Meta:
        unique_together = [("student", "course")]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.student} → {self.course}"

    @property
    def progress_percent(self) -> int:
        total = self.course.lessons.count()
        if not total:
            return 0
        completed = self.lesson_progress.filter(completed_at__isnull=False).count()
        return round(completed / total * 100)

    @property
    def is_complete(self) -> bool:
        return self.progress_percent == 100


class LessonProgress(BaseModel):
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress_records")
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("enrollment", "lesson")]

    def __str__(self) -> str:
        return f"{self.enrollment} — {self.lesson}"
