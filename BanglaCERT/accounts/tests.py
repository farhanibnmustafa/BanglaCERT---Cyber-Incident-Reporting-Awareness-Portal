from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from incidents.models import Incident


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

    def test_normal_user_login_honors_safe_next_redirect(self):
        user = User.objects.create_user(
            username="reader1",
            email="reader1@example.com",
            password="pass12345",
        )
        incident = Incident.objects.create(
            title="Verified Awareness Post",
            category="phishing",
            description="Visible awareness post.",
            incident_date="2026-03-01",
            status=Incident.STATUS_VERIFIED,
            created_by=user,
        )
        next_url = reverse("awareness:detail", args=[incident.id])

        response = self.client.post(
            f"{reverse('accounts:login')}?next={next_url}",
            {"email": "reader1@example.com", "password": "pass12345", "next": next_url},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, next_url)

    def test_registration_honors_safe_next_redirect(self):
        user = User.objects.create_user(
            username="reader2",
            email="reader2@example.com",
            password="pass12345",
        )
        incident = Incident.objects.create(
            title="Verified Awareness Post 2",
            category="malware",
            description="Visible awareness post for registration redirect.",
            incident_date="2026-03-02",
            status=Incident.STATUS_VERIFIED,
            created_by=user,
        )
        next_url = reverse("awareness:detail", args=[incident.id])

        response = self.client.post(
            f"{reverse('accounts:register')}?next={next_url}",
            {
                "email": "brandnew@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "next": next_url,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, next_url)

    def test_staff_login_page_is_available(self):
        response = self.client.get(reverse("accounts:staff_login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Staff Sign In")
        self.assertNotContains(response, "Create an Account")
        self.assertContains(response, "User Login")

    def test_root_staff_login_shortcut_redirects_to_accounts_staff_login(self):
        response = self.client.get("/staff-login/")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:staff_login"))

    def test_normal_user_cannot_sign_in_from_staff_login_page(self):
        User.objects.create_user(
            username="normal2",
            email="normal2@example.com",
            password="pass12345",
        )

        response = self.client.post(
            reverse("accounts:staff_login"),
            {"email": "normal2@example.com", "password": "pass12345"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This login page is for staff users only.")

    def test_staff_user_can_sign_in_from_staff_login_page(self):
        User.objects.create_user(
            username="staff3",
            email="staff3@example.com",
            password="pass12345",
            is_staff=True,
        )

        response = self.client.post(
            reverse("accounts:staff_login"),
            {"email": "staff3@example.com", "password": "pass12345"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/", response.url)
