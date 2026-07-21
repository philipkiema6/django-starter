import os

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Idempotently creates one superuser from DJANGO_SUPERUSER_EMAIL /
    DJANGO_SUPERUSER_PASSWORD, for hosts (e.g. Render's free tier) with no shell access to run
    `createsuperuser` interactively. Safe to run on every deploy:

    - No-ops if either variable is unset.
    - No-ops if a user with that email already exists — never touches an existing account's
      password, so leaving the env vars set permanently is safe.
    - Never writes the password to stdout/logs.
    """

    help = "Create a superuser from DJANGO_SUPERUSER_EMAIL/DJANGO_SUPERUSER_PASSWORD if one doesn't already exist."

    def handle(self, **options):
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not email or not password:
            self.stdout.write("DJANGO_SUPERUSER_EMAIL/DJANGO_SUPERUSER_PASSWORD not set — skipping.")
            return

        user_model = get_user_model()
        username_field = user_model.USERNAME_FIELD

        # The allauth adapter stores email in the username field for normal signups; match on
        # both so this is a no-op if the account was instead created some other way.
        exists = user_model.objects.filter(email__iexact=email).exists() or (
            username_field != "email" and user_model.objects.filter(**{f"{username_field}__iexact": email}).exists()
        )
        if exists:
            self.stdout.write(f"Superuser '{email}' already exists — skipping (existing password left untouched).")
            return

        create_kwargs = {"email": email, "password": password}
        if username_field != "email":
            create_kwargs[username_field] = email
        user = user_model.objects.create_superuser(**create_kwargs)
        EmailAddress.objects.create(user=user, email=user.email, primary=True, verified=True)
        self.stdout.write(self.style.SUCCESS(f"Created superuser '{email}'."))
