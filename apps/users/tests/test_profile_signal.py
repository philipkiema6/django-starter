from django.test import TestCase

from apps.users.models import CustomUser, Profile


class ProfileSignalTest(TestCase):
    def test_profile_created_on_user_creation(self):
        user = CustomUser.objects.create_user(username="new@example.com", email="new@example.com", password="pw")
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_default_role_is_student(self):
        user = CustomUser.objects.create_user(username="new@example.com", email="new@example.com", password="pw")
        self.assertEqual(user.profile.role, Profile.ROLE_STUDENT)
        self.assertTrue(user.profile.is_student)
        self.assertFalse(user.profile.is_instructor)

    def test_signal_does_not_duplicate_profile_on_save(self):
        user = CustomUser.objects.create_user(username="new@example.com", email="new@example.com", password="pw")
        user.first_name = "Updated"
        user.save()
        self.assertEqual(Profile.objects.filter(user=user).count(), 1)
