from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.activity.helpers import log_activity
from apps.activity.models import ActivityLog
from apps.users.models import CustomUser, Profile

from .forms import AdminCreateUserForm
from .permissions import staff_required
from .selectors import dashboard_stats

USERS_PER_PAGE = 25
LOGS_PER_PAGE = 25


@staff_required
def dashboard(request):
    return render(
        request,
        "adminpanel/dashboard.html",
        {**dashboard_stats(), "active_tab": "admin_dashboard", "page_title": _("Admin Dashboard")},
    )


@staff_required
def user_list(request):
    role_filter = request.GET.get("role", "")
    users = CustomUser.objects.select_related("profile").order_by("-date_joined")
    if role_filter in (Profile.ROLE_STUDENT, Profile.ROLE_INSTRUCTOR):
        users = users.filter(profile__role=role_filter)

    page = Paginator(users, USERS_PER_PAGE).get_page(request.GET.get("page"))
    return render(
        request,
        "adminpanel/user_list.html",
        {
            "page_obj": page,
            "role_filter": role_filter,
            "active_tab": "admin_users",
            "page_title": _("Users"),
        },
    )


@staff_required
def user_create(request):
    if request.method == "POST":
        form = AdminCreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_activity(
                actor=request.user,
                action="user.created",
                description=(
                    f"{request.user.get_display_name()} created an account for {user.email} "
                    f"({user.profile.get_role_display()})"
                ),
            )
            messages.success(request, _("Account created for %(email)s.") % {"email": user.email})
            return redirect("adminpanel:user_list")
    else:
        form = AdminCreateUserForm()
    return render(
        request,
        "adminpanel/user_create.html",
        {"form": form, "active_tab": "admin_users", "page_title": _("New Account")},
    )


@staff_required
@require_POST
def user_toggle_active(request, user_id):
    target = get_object_or_404(CustomUser, pk=user_id)
    if target.pk == request.user.pk:
        messages.error(request, _("You cannot deactivate your own account."))
        return redirect("adminpanel:user_list")
    if target.is_superuser and not request.user.is_superuser:
        raise PermissionDenied

    target.is_active = not target.is_active
    target.save(update_fields=["is_active"])
    action = "activated" if target.is_active else "deactivated"
    log_activity(
        actor=request.user,
        action=f"user.{action}",
        description=f"{request.user.get_display_name()} {action} {target.email}",
    )
    messages.success(request, _("Account updated."))
    return redirect("adminpanel:user_list")


@staff_required
def logs(request):
    entries = ActivityLog.objects.select_related("actor")
    page = Paginator(entries, LOGS_PER_PAGE).get_page(request.GET.get("page"))
    return render(
        request,
        "adminpanel/logs.html",
        {"page_obj": page, "active_tab": "admin_logs", "page_title": _("Activity Log")},
    )
