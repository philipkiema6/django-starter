from django.conf import settings
from django.db import models

from apps.utils.models import BaseModel


class ActivityLog(BaseModel):
    """A simple, append-only record of notable events for the admin activity feed. Written via
    apps.activity.helpers.log_activity() from wherever the event actually happens (views,
    signals) rather than inferred generically, so entries stay human-readable."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="activity_logs"
    )
    action = models.CharField(max_length=50)
    description = models.CharField(max_length=255)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.description
