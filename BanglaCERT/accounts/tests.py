from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


User = get_user_model()


class AccountFlowTests(TestCase):
    def test_normal_user_registration_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "email": "newuser@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="newuser@example.com")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertNotEqual(user.password, "StrongPass123!")
        self.assertTrue(user.check_password("StrongPass123!"))
        self.assertIn("_auth_user_id", self.client.session)

    def test_duplicate_email_registration_rejected(self):
        User.objects.create_user(
            username="u1",
            email="dupe@example.com",
            password="pass12345",
        )

        response = self.client.post(
            reverse("accounts:register"),
            {
                "email": "dupe@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email="dupe@example.com").count(), 1)

    def test_staff_login_redirects_to_admin(self):
        User.objects.create_user(
            username="staff1",
            email="staff1@example.com",
            password="pass12345",
            is_staff=True,
        )

        response = self.client.post(
            reverse("accounts:login"),
            {"email": "staff1@example.com", "password": "pass12345"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/", response.url)

    def test_staff_login_with_username_redirects_to_admin(self):
        User.objects.create_user(
            username="staff2",
            email="staff2@example.com",
            password="pass12345",
            is_staff=True,
        )

        response = self.client.post(
            reverse("accounts:login"),
            {"email": "staff2", "password": "pass12345"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/", response.url)

    def test_normal_user_login_with_email_redirects_to_incidents(self):
        User.objects.create_user(
            username="normal1",
            email="normal1@example.com",
            password="pass12345",
        )

        response = self.client.post(
            reverse("accounts:login"),
            {"email": "normal1@example.com", "password": "pass12345"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/incidents/mine/", response.url)
