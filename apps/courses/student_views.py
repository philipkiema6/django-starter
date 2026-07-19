from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.activity.helpers import log_activity

from .certificates import generate_certificate_pdf
from .models import Course, Enrollment, Lesson, LessonProgress
from .permissions import student_required

COURSES_PER_PAGE = 12


def catalog(request):
    courses = (
        Course.objects.filter(is_published=True)
        .select_related("instructor", "instructor__profile")
        .prefetch_related("lessons")
    )
    paginator = Paginator(courses, COURSES_PER_PAGE)
    page = paginator.get_page(request.GET.get("page"))

    enrolled_slugs = set()
    if request.user.is_authenticated:
        enrolled_slugs = set(
            Enrollment.objects.filter(student=request.user, course__in=page.object_list).values_list(
                "course__slug", flat=True
            )
        )

    context = {
        "page_obj": page,
        "is_paginated": page.has_other_pages(),
        "elided_page_range": page.paginator.get_elided_page_range(page.number),
        "enrolled_slugs": enrolled_slugs,
        "active_tab": "catalog",
        "page_title": _("Browse Courses"),
    }
    template = "courses/components/course_grid.html" if request.htmx else "courses/catalog.html"
    return render(request, template, context)


def detail(request, slug):
    course = get_object_or_404(Course.objects.select_related("instructor", "instructor__profile"), slug=slug)
    enrollment = None
    if request.user.is_authenticated:
        enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    return render(
        request,
        "courses/detail.html",
        {
            "course": course,
            "enrollment": enrollment,
            "lesson_count": course.lessons.count(),
            "active_tab": "catalog",
            "page_title": course.title,
        },
    )


@student_required
@require_POST
def enroll(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    enrollment, created = Enrollment.objects.get_or_create(student=request.user, course=course)
    if created:
        log_activity(
            actor=request.user,
            action="enrollment.created",
            description=f"{request.user.get_display_name()} enrolled in “{course.title}”",
        )
    return render(request, "courses/components/enroll_button.html", {"course": course, "enrollment": enrollment})


@login_required
def my_learning(request):
    enrollments = (
        Enrollment.objects.filter(student=request.user)
        .select_related("course")
        .prefetch_related("course__lessons", "lesson_progress")
    )
    return render(
        request,
        "courses/my_learning.html",
        {"enrollments": enrollments, "active_tab": "my_learning", "page_title": _("My Enrollments")},
    )


@login_required
def learn(request, slug):
    """Entry point for a student's course workspace: jump straight to the first lesson."""
    course = get_object_or_404(Course, slug=slug)
    get_object_or_404(Enrollment, student=request.user, course=course)
    first_lesson = course.lessons.first()
    if first_lesson is None:
        return render(
            request,
            "courses/learn_empty.html",
            {"course": course, "active_tab": "my_learning", "page_title": course.title},
        )
    return redirect("courses:lesson", slug=slug, lesson_id=first_lesson.pk)


@login_required
def lesson_view(request, slug, lesson_id):
    course = get_object_or_404(Course, slug=slug)
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    lesson = get_object_or_404(Lesson, pk=lesson_id, course=course)
    lessons = list(course.lessons.all())
    current_index = next((i for i, item in enumerate(lessons) if item.pk == lesson.pk), 0)
    next_lesson = lessons[current_index + 1] if current_index + 1 < len(lessons) else None
    completed_lesson_ids = set(
        LessonProgress.objects.filter(enrollment=enrollment, completed_at__isnull=False).values_list(
            "lesson_id", flat=True
        )
    )
    return render(
        request,
        "courses/learn.html",
        {
            "course": course,
            "enrollment": enrollment,
            "lessons": lessons,
            "current_lesson": lesson,
            "next_lesson": next_lesson,
            "completed_lesson_ids": completed_lesson_ids,
            "lesson_is_complete": lesson.pk in completed_lesson_ids,
            "active_tab": "my_learning",
            "page_title": lesson.title,
        },
    )


@login_required
@require_POST
def mark_lesson_complete(request, slug, lesson_id):
    course = get_object_or_404(Course, slug=slug)
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    lesson = get_object_or_404(Lesson, pk=lesson_id, course=course)
    _progress, created = LessonProgress.objects.update_or_create(
        enrollment=enrollment, lesson=lesson, defaults={"completed_at": timezone.now()}
    )
    if created:
        log_activity(
            actor=request.user,
            action="lesson.completed",
            description=f"{request.user.get_display_name()} completed “{lesson.title}” in “{course.title}”",
        )
        if enrollment.is_complete:
            log_activity(
                actor=request.user,
                action="course.completed",
                description=f"{request.user.get_display_name()} completed the course “{course.title}”",
            )
    lessons = list(course.lessons.all())
    current_index = next((i for i, item in enumerate(lessons) if item.pk == lesson.pk), 0)
    next_lesson = lessons[current_index + 1] if current_index + 1 < len(lessons) else None
    return render(
        request,
        "courses/components/lesson_complete_response.html",
        {"course": course, "enrollment": enrollment, "next_lesson": next_lesson},
    )


@login_required
def certificate(request, slug):
    course = get_object_or_404(Course, slug=slug)
    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)
    if not enrollment.is_complete:
        messages.error(request, _("Complete every lesson in this course to unlock your certificate."))
        return redirect("courses:learn", slug=slug)

    pdf_bytes = generate_certificate_pdf(enrollment)
    log_activity(
        actor=request.user,
        action="certificate.downloaded",
        description=f"{request.user.get_display_name()} downloaded their certificate for “{course.title}”",
    )
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="certificate-{course.slug}.pdf"'
    return response
