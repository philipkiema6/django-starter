from apps.activity.models import ActivityLog
from apps.courses.models import Course, Enrollment
from apps.users.models import CustomUser, Profile


def dashboard_stats() -> dict:
    return {
        "total_users": CustomUser.objects.count(),
        "total_instructors": Profile.objects.filter(role=Profile.ROLE_INSTRUCTOR).count(),
        "total_students": Profile.objects.filter(role=Profile.ROLE_STUDENT).count(),
        "active_users": CustomUser.objects.filter(is_active=True).count(),
        "inactive_users": CustomUser.objects.filter(is_active=False).count(),
        "total_courses": Course.objects.count(),
        "published_courses": Course.objects.filter(is_published=True).count(),
        "total_enrollments": Enrollment.objects.count(),
        "recent_activity": ActivityLog.objects.select_related("actor")[:10],
    }
