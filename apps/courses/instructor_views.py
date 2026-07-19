from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

from apps.activity.helpers import log_activity

from .forms import CourseForm, LessonForm
from .models import Course, Lesson
from .permissions import instructor_required


def _get_owned_course(request, slug):
    return get_object_or_404(Course, slug=slug, instructor=request.user)


@instructor_required
def course_list(request):
    courses = Course.objects.filter(instructor=request.user).prefetch_related("lessons")
    return render(
        request,
        "courses/instructor/course_list.html",
        {"courses": courses, "active_tab": "my_courses", "page_title": _("My Courses")},
    )


@instructor_required
def course_create(request):
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            log_activity(
                actor=request.user,
                action="course.created",
                description=f"{request.user.get_display_name()} created the course “{course.title}”",
            )
            messages.success(request, _("Course created. Now add some lessons!"))
            return redirect("courses:instructor_course_detail", slug=course.slug)
    else:
        form = CourseForm()
    return render(
        request,
        "courses/instructor/course_form.html",
        {"form": form, "active_tab": "my_courses", "page_title": _("New Course")},
    )


@instructor_required
def course_detail(request, slug):
    course = _get_owned_course(request, slug)
    return render(
        request,
        "courses/instructor/course_detail.html",
        {
            "course": course,
            "lessons": course.lessons.all(),
            "enrollments": course.enrollments.select_related("student"),
            "active_tab": "my_courses",
            "page_title": course.title,
        },
    )


@instructor_required
def course_edit(request, slug):
    course = _get_owned_course(request, slug)
    was_published = course.is_published
    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            if course.is_published and not was_published:
                log_activity(
                    actor=request.user,
                    action="course.published",
                    description=f"{request.user.get_display_name()} published the course “{course.title}”",
                )
            messages.success(request, _("Course updated."))
            return redirect("courses:instructor_course_detail", slug=course.slug)
    else:
        form = CourseForm(instance=course)
    return render(
        request,
        "courses/instructor/course_form.html",
        {"form": form, "course": course, "active_tab": "my_courses", "page_title": _("Edit Course")},
    )


@instructor_required
def course_delete(request, slug):
    course = _get_owned_course(request, slug)
    if request.method == "POST":
        course.delete()
        messages.success(request, _("Course deleted."))
        return redirect("courses:instructor_course_list")
    return redirect("courses:instructor_course_detail", slug=slug)


@instructor_required
def lesson_create(request, course_slug):
    course = _get_owned_course(request, course_slug)
    if request.method == "POST":
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            messages.success(request, _("Lesson added."))
            return redirect("courses:instructor_course_detail", slug=course.slug)
    else:
        form = LessonForm(initial={"order": course.lessons.count()})
    return render(
        request,
        "courses/instructor/lesson_form.html",
        {"form": form, "course": course, "active_tab": "my_courses", "page_title": _("New Lesson")},
    )


@instructor_required
def lesson_edit(request, course_slug, lesson_id):
    course = _get_owned_course(request, course_slug)
    lesson = get_object_or_404(Lesson, pk=lesson_id, course=course)
    if request.method == "POST":
        form = LessonForm(request.POST, instance=lesson)
        if form.is_valid():
            form.save()
            messages.success(request, _("Lesson updated."))
            return redirect("courses:instructor_course_detail", slug=course.slug)
    else:
        form = LessonForm(instance=lesson)
    return render(
        request,
        "courses/instructor/lesson_form.html",
        {"form": form, "course": course, "lesson": lesson, "active_tab": "my_courses", "page_title": _("Edit Lesson")},
    )


@instructor_required
def lesson_delete(request, course_slug, lesson_id):
    course = _get_owned_course(request, course_slug)
    lesson = get_object_or_404(Lesson, pk=lesson_id, course=course)
    if request.method == "POST":
        lesson.delete()
        messages.success(request, _("Lesson deleted."))
    return redirect("courses:instructor_course_detail", slug=course.slug)
