from django.urls import path

from . import instructor_views, student_views

app_name = "courses"
urlpatterns = [
    # instructor-facing course management
    path("manage/", instructor_views.course_list, name="instructor_course_list"),
    path("manage/new/", instructor_views.course_create, name="instructor_course_create"),
    path("manage/<slug:slug>/", instructor_views.course_detail, name="instructor_course_detail"),
    path("manage/<slug:slug>/edit/", instructor_views.course_edit, name="instructor_course_edit"),
    path("manage/<slug:slug>/delete/", instructor_views.course_delete, name="instructor_course_delete"),
    path("manage/<slug:course_slug>/lessons/new/", instructor_views.lesson_create, name="instructor_lesson_create"),
    path(
        "manage/<slug:course_slug>/lessons/<int:lesson_id>/edit/",
        instructor_views.lesson_edit,
        name="instructor_lesson_edit",
    ),
    path(
        "manage/<slug:course_slug>/lessons/<int:lesson_id>/delete/",
        instructor_views.lesson_delete,
        name="instructor_lesson_delete",
    ),
    # student-facing browsing / learning
    path("my-learning/", student_views.my_learning, name="my_learning"),
    path("", student_views.catalog, name="catalog"),
    path("<slug:slug>/", student_views.detail, name="detail"),
    path("<slug:slug>/enroll/", student_views.enroll, name="enroll"),
    path("<slug:slug>/learn/", student_views.learn, name="learn"),
    path("<slug:slug>/learn/<int:lesson_id>/", student_views.lesson_view, name="lesson"),
    path("<slug:slug>/learn/<int:lesson_id>/complete/", student_views.mark_lesson_complete, name="mark_complete"),
    path("<slug:slug>/certificate/", student_views.certificate, name="certificate"),
]
