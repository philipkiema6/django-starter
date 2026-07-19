from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def instructor_required(view_func):
    """Reject non-instructors with a 403. Login is enforced separately via @login_required."""

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.profile.is_instructor:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped


def student_required(view_func):
    """Reject non-students with a 403 (e.g. instructors trying to enroll in a course)."""

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.profile.is_student:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped
