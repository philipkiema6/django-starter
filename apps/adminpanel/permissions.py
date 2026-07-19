from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def staff_required(view_func):
    """Gate a view to Django staff/superuser accounts — the "Admin" role in this app,
    reusing Django's built-in is_staff flag rather than adding a third Profile.role value."""

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped
