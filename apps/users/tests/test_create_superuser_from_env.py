import os

from allauth.account.models import EmailAddress
from django.core.management import call_command
from django.test import TestCase

from apps.users.models import CustomUser

ENV_VARS = ("DJANGO_SUPERUSER_EMAIL", "DJANGO_SUPERUSER_PASSWORD")


class CreateSuperuserFromEnvTest(TestCase):
    def tearDown(self):
        for var in ENV_VARS:
            os.environ.pop(var, None)
        super().tearDown()

    def test_noop_when_env_vars_unset(self):
        call_command("create_superuser_from_env")
        self.assertEqual(CustomUser.objects.count(), 0)

    def test_creates_superuser_from_env_vars(self):
        os.environ["DJANGO_SUPERUSER_EMAIL"] = "bootstrap@example.com"
        os.environ["DJANGO_SUPERUSER_PASSWORD"] = "BootstrapPassword123!"
        call_command("create_superuser_from_env")

        user = CustomUser.objects.get(email__iexact="bootstrap@example.com")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.check_password("BootstrapPassword123!"))
        self.assertTrue(EmailAddress.objects.filter(user=user, verified=True, primary=True).exists())

    def test_does_not_overwrite_existing_password(self):
        CustomUser.objects.create_superuser(
            username="bootstrap@example.com", email="bootstrap@example.com", password="OriginalPassword123!"
        )
        os.environ["DJANGO_SUPERUSER_EMAIL"] = "bootstrap@example.com"
        os.environ["DJANGO_SUPERUSER_PASSWORD"] = "AttemptedOverwrite456!"
        call_command("create_superuser_from_env")

        self.assertEqual(CustomUser.objects.filter(email__iexact="bootstrap@example.com").count(), 1)
        user = CustomUser.objects.get(email__iexact="bootstrap@example.com")
        self.assertTrue(user.check_password("OriginalPassword123!"))
