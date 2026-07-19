from django.urls import reverse

from .base import AdminPanelTestBase


class AdminPanelPermissionsTest(AdminPanelTestBase):
    def test_student_cannot_access_dashboard(self):
        response = self.student_client.get(reverse("adminpanel:dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_student_cannot_access_user_list(self):
        response = self.student_client.get(reverse("adminpanel:user_list"))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_redirected_to_login(self):
        url = reverse("adminpanel:dashboard")
        response = self.client.get(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")

    def test_staff_can_access_dashboard(self):
        response = self.staff_client.get(reverse("adminpanel:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_staff_home_redirects_to_admin_dashboard(self):
        response = self.staff_client.get(reverse("web:home"))
        self.assertRedirects(response, reverse("adminpanel:dashboard"))
