"""Small read-query helpers, kept out of apps.web so that app doesn't need to know about
courses' ORM details beyond calling these two functions for its dashboard."""

from .models import Course, Enrollment


def instructor_dashboard_data(user) -> dict:
    courses = Course.objects.filter(instructor=user).prefetch_related("lessons")
    return {
        "courses": courses,
        "course_count": courses.count(),
        "published_count": courses.filter(is_published=True).count(),
        "student_count": Enrollment.objects.filter(course__instructor=user).count(),
    }


def student_dashboard_data(user) -> dict:
    enrollments = (
        Enrollment.objects.filter(student=user)
        .select_related("course")
        .prefetch_related("course__lessons", "lesson_progress")
    )
    return {
        "enrollments": enrollments,
        "enrollment_count": enrollments.count(),
    }
