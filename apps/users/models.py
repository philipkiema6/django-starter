import hashlib
import uuid
from functools import cached_property

from allauth.account.models import EmailAddress
from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.users.helpers import validate_profile_picture
from apps.utils.models import BaseModel


def _get_avatar_filename(instance, filename):
    """Use random filename prevent overwriting existing files & to fix caching issues."""
    return f"profile-pictures/{uuid.uuid4()}.{filename.split('.')[-1]}"


class CustomUser(AbstractUser):
    """
    Add additional fields to the user model here.
    """

    avatar = models.FileField(upload_to=_get_avatar_filename, blank=True, validators=[validate_profile_picture])

    def __str__(self):
        return f"{self.get_full_name()} <{self.email or self.username}>"

    def get_display_name(self) -> str:
        if self.get_full_name().strip():
            return self.get_full_name()
        return self.email or self.username

    @property
    def avatar_url(self) -> str:
        if self.avatar:
            return self.avatar.url
        else:
            return f"https://www.gravatar.com/avatar/{self.gravatar_id}?s=128&d=identicon"

    @property
    def gravatar_id(self) -> str:
        # https://en.gravatar.com/site/implement/hash/
        return hashlib.md5(self.email.lower().strip().encode("utf-8")).hexdigest()

    @cached_property
    def has_verified_email(self):
        return EmailAddress.objects.filter(user=self, verified=True).exists()


class Profile(BaseModel):
    """
    Every CustomUser gets a Profile (see apps.users.signals.create_profile), which carries
    role and other user-facing details that don't belong on the auth model itself.
    """

    ROLE_STUDENT = "student"
    ROLE_INSTRUCTOR = "instructor"
    ROLE_CHOICES = [
        (ROLE_STUDENT, "Student"),
        (ROLE_INSTRUCTOR, "Instructor"),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    bio = models.TextField(blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=120, blank=True)

    def __str__(self) -> str:
        return f"{self.user} ({self.role})"

    @property
    def is_instructor(self) -> bool:
        return self.role == self.ROLE_INSTRUCTOR

    @property
    def is_student(self) -> bool:
        return self.role == self.ROLE_STUDENT
