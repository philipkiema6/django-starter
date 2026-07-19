from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fields = ("role", "bio", "phone_number", "location")


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ("username", "email", "first_name", "last_name", "role", "is_staff", "date_joined")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups", "profile__role", "date_joined")
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined",)

    fieldsets = UserAdmin.fieldsets + (
        (
            "Custom Fields",
            {"fields": ("avatar",)},
        ),
    )  # type: ignore

    @admin.display(description="Role")
    def role(self, obj: CustomUser) -> str:
        return obj.profile.get_role_display()
