from django.test import Client
from django.urls import reverse

from apps.activity.models import ActivityLog
from apps.users.models import CustomUser, Profile

from .base import AdminPanelTestBase


class UserCreationTest(AdminPanelTestBase):
    def test_admin_can_create_instructor_account(self):
        response = self.staff_client.post(
            reverse("adminpanel:user_create"),
            {
                "email": "new-instructor@example.com",
                "first_name": "New",
                "last_name": "Instructor",
                "role": Profile.ROLE_INSTRUCTOR,
                "password": "a-strong-password",
            },
        )
        self.assertRedirects(response, reverse("adminpanel:user_list"))
        user = CustomUser.objects.get(email="new-instructor@example.com")
        self.assertTrue(user.is_active)
        self.assertEqual(user.profile.role, Profile.ROLE_INSTRUCTOR)

    def test_created_account_can_log_in(self):
        self.staff_client.post(
            reverse("adminpanel:user_create"),
            {
                "email": "loginable@example.com",
                "first_name": "Log",
                "last_name": "Inable",
                "role": Profile.ROLE_STUDENT,
                "password": "a-strong-password",
            },
        )
        client = Client()
        self.assertTrue(client.login(username="loginable@example.com", password="a-strong-password"))

    def test_duplicate_email_rejected(self):
        response = self.staff_client.post(
            reverse("adminpanel:user_create"),
            {
                "email": self.student.email,
                "first_name": "Dup",
                "last_name": "Licate",
                "role": Profile.ROLE_STUDENT,
                "password": "a-strong-password",
            },
        )
        self.assertEqual(response.status_code, 200)  # re-rendered form with errors
        self.assertFalse(CustomUser.objects.filter(email=self.student.email, first_name="Dup").exists())

    def test_creation_logs_activity(self):
        self.staff_client.post(
            reverse("adminpanel:user_create"),
            {
                "email": "logged@example.com",
                "first_name": "Log",
                "last_name": "Ged",
                "role": Profile.ROLE_STUDENT,
                "password": "a-strong-password",
            },
        )
        self.assertTrue(ActivityLog.objects.filter(action="user.created").exists())


class UserDeactivationTest(AdminPanelTestBase):
    def test_admin_can_deactivate_a_student(self):
        response = self.staff_client.post(reverse("adminpanel:user_toggle_active", args=[self.student.pk]))
        self.assertRedirects(response, reverse("adminpanel:user_list"))
        self.student.refresh_from_db()
        self.assertFalse(self.student.is_active)

    def test_deactivate_then_activate_toggles_back(self):
        url = reverse("adminpanel:user_toggle_active", args=[self.student.pk])
        self.staff_client.post(url)
        self.staff_client.post(url)
        self.student.refresh_from_db()
        self.assertTrue(self.student.is_active)

    def test_admin_cannot_deactivate_self(self):
        self.staff_client.post(reverse("adminpanel:user_toggle_active", args=[self.staff.pk]))
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.is_active)

    def test_deactivated_user_is_logged_out_on_next_request(self):
        client = Client()
        client.force_login(self.student)
        self.staff_client.post(reverse("adminpanel:user_toggle_active", args=[self.student.pk]))

        response = client.get(reverse("courses:catalog"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_deactivated_user_cannot_log_in(self):
        self.staff_client.post(reverse("adminpanel:user_toggle_active", args=[self.student.pk]))
        client = Client()
        self.assertFalse(client.login(username=self.student.username, password="password123"))

    def test_deactivation_logs_activity(self):
        self.staff_client.post(reverse("adminpanel:user_toggle_active", args=[self.student.pk]))
        self.assertTrue(ActivityLog.objects.filter(action="user.deactivated").exists())
