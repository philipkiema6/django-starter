from django.contrib import admin

from .models import Course, Enrollment, Lesson, LessonProgress


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ("title", "order")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "instructor", "is_published", "student_count", "created_at")
    list_filter = ("is_published", "created_at")
    search_fields = ("title", "instructor__email", "instructor__first_name", "instructor__last_name")
    prepopulated_fields = {"slug": ("title",)}
    inlines = (LessonInline,)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order")
    list_filter = ("course",)
    search_fields = ("title", "course__title")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """Admins can enroll (or remove) any student in any course from here."""

    list_display = ("student", "course", "progress_percent", "created_at")
    list_filter = ("course",)
    search_fields = ("student__email", "course__title")
    autocomplete_fields = ("student", "course")


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "lesson", "completed_at")
    list_filter = ("lesson__course",)
