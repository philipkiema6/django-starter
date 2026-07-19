from .models import ActivityLog


def log_activity(actor, action: str, description: str) -> ActivityLog:
    """actor may be None (e.g. for events with no clear human actor)."""
    return ActivityLog.objects.create(actor=actor, action=action, description=description)
