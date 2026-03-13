from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.core import mail
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import timezone

from auditlog.models import AuditLog

from .models import Incident, IncidentComment


User = get_user_model()


class IncidentWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="normaluser", password="pass12345")
        self.other_user = User.objects.create_user(username="otheruser", password="pass12345")
        self.manager_user = User.objects.create_user(
            username="systemadmin40329",
            email="manager@example.com",
            password="pass12345",
            is_staff=True,
            is_superuser=True,
        )
        self.staff_user = User.objects.create_user(
            username="adminuser",
            password="pass12345",
            is_staff=True,
        )

    def test_normal_user_can_report_incident(self):
        self.client.login(username="normaluser", password="pass12345")
        response = self.client.post(
            reverse("incidents:report"),
            {
                "title": "Suspicious Email",
                "category": "phishing",
                "description": "A phishing message asked for credentials.",
                "incident_date": "2026-03-01",
            },
        )

        self.assertEqual(response.status_code, 302)
        incident = Incident.objects.get(title="Suspicious Email")
        self.assertEqual(incident.created_by, self.user)
        self.assertEqual(incident.status, Incident.STATUS_PENDING)

    def test_guest_user_can_submit_anonymous_report(self):
        response = self.client.post(
            reverse("incidents:public_report"),
            {
                "title": "Anonymous Email Scam",
                "category": "phishing",
                "description": "Guest submitted phishing report.",
                "incident_date": "2026-03-02",
                "reporter_email": "guest@example.com",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("incidents:public_report_success"))
        incident = Incident.objects.get(title="Anonymous Email Scam")
        self.assertIsNone(incident.created_by)
        self.assertTrue(incident.is_anonymous)
        self.assertEqual(incident.reporter_email, "guest@example.com")

    def test_normal_user_cannot_view_other_users_incident(self):
        own_incident = Incident.objects.create(
            title="Own Incident",
            category="fraud",
            description="Own record",
            incident_date=date(2026, 3, 1),
            created_by=self.user,
        )
        other_incident = Incident.objects.create(
            title="Other Incident",
            category="fraud",
            description="Other record",
            incident_date=date(2026, 3, 1),
            created_by=self.other_user,
        )

        self.client.login(username="normaluser", password="pass12345")
        own_response = self.client.get(reverse("incidents:detail", args=[own_incident.id]))
        other_response = self.client.get(reverse("incidents:detail", args=[other_incident.id]))

        self.assertEqual(own_response.status_code, 200)
        self.assertEqual(other_response.status_code, 404)

    def test_staff_user_redirected_to_custom_admin_from_user_portal(self):
        incident = Incident.objects.create(
            title="Any Incident",
            category="other",
            description="Details",
            incident_date=date(2026, 3, 1),
            created_by=self.user,
        )

        self.client.login(username="adminuser", password="pass12345")
        home_response = self.client.get(reverse("incidents:home"))
        report_response = self.client.get(reverse("incidents:report"))
        list_response = self.client.get(reverse("incidents:my_incidents"))
        detail_response = self.client.get(reverse("incidents:detail", args=[incident.id]))

        self.assertEqual(home_response.status_code, 302)
        self.assertEqual(report_response.status_code, 302)
        self.assertEqual(list_response.status_code, 302)
        self.assertEqual(detail_response.status_code, 302)
        self.assertIn("/admin/", home_response.url)
        self.assertIn("/admin/", report_response.url)
        self.assertIn("/admin/", list_response.url)
        self.assertIn("/admin/", detail_response.url)

    def test_normal_user_can_comment_only_on_own_incident(self):
        own_incident = Incident.objects.create(
            title="Own Incident",
            category="other",
            description="Details",
            incident_date=date(2026, 3, 1),
            created_by=self.user,
        )
        other_incident = Incident.objects.create(
            title="Other Incident",
            category="other",
            description="Details",
            incident_date=date(2026, 3, 1),
            created_by=self.other_user,
        )

        self.client.login(username="normaluser", password="pass12345")
        own_comment_response = self.client.post(
            reverse("incidents:add_comment", args=[own_incident.id]),
            {"comment": "Please review this quickly."},
        )
        other_comment_response = self.client.post(
            reverse("incidents:add_comment", args=[other_incident.id]),
            {"comment": "I should not be able to add this."},
        )

        self.assertEqual(own_comment_response.status_code, 302)
        self.assertEqual(other_comment_response.status_code, 404)
        self.assertEqual(IncidentComment.objects.filter(incident=own_incident).count(), 1)
        self.assertEqual(IncidentComment.objects.filter(incident=other_incident).count(), 0)

    def test_staff_user_cannot_comment_from_user_endpoint(self):
        incident = Incident.objects.create(
            title="User Incident",
            category="other",
            description="Details",
            incident_date=date(2026, 3, 1),
            created_by=self.user,
        )

        self.client.login(username="adminuser", password="pass12345")
        response = self.client.post(
            reverse("incidents:add_comment", args=[incident.id]),
            {"comment": "Admin should comment from admin only."},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/", response.url)
        self.assertEqual(IncidentComment.objects.filter(incident=incident).count(), 0)

    def test_staff_user_can_open_custom_admin_dashboard(self):
        Incident.objects.create(
            title="Queue Item",
            category="phishing",
            description="Needs review",
            incident_date=date(2026, 3, 1),
            created_by=self.user,
        )

        self.client.login(username="adminuser", password="pass12345")
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "incidents/admin_dashboard.html")
        self.assertContains(response, "Queue Item")

    def test_staff_dashboard_navigation_shows_single_dashboard_link(self):
        self.client.login(username="adminuser", password="pass12345")
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'href="{reverse("admin:index")}">Dashboard</a>')
        self.assertNotContains(response, f'href="{reverse("incidents:home")}">Home</a>')
        self.assertNotContains(response, 'href="/admin/">Admin Dashboard</a>')

    @override_settings(TIME_ZONE="Asia/Dhaka", USE_TZ=True)
    def test_my_reports_display_submitted_time_in_dhaka_timezone(self):
        incident = Incident.objects.create(
            title="Timezone Incident",
            category="other",
            description="Timezone check",
            incident_date=date(2026, 3, 1),
            created_by=self.user,
        )
        utc_time = datetime(2026, 3, 14, 0, 30, tzinfo=ZoneInfo("UTC"))
        Incident.objects.filter(pk=incident.pk).update(created_at=utc_time, updated_at=utc_time)

        self.client.login(username="normaluser", password="pass12345")
        response = self.client.get(reverse("incidents:my_incidents"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "2026-03-14 06:30")

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_staff_user_can_update_status_from_custom_admin(self):
        self.user.email = "normaluser@example.com"
        self.user.save(update_fields=["email"])
        incident = Incident.objects.create(
            title="Status Update",
            category="other",
            description="Needs staff update",
            incident_date=date(2026, 3, 1),
            created_by=self.user,
        )

        self.client.login(username="adminuser", password="pass12345")
        response = self.client.post(
            reverse("admin:incident_status", args=[incident.id]),
            {"status": Incident.STATUS_VERIFIED},
        )

        self.assertEqual(response.status_code, 302)
        incident.refresh_from_db()
        self.assertEqual(incident.status, Incident.STATUS_VERIFIED)
        self.assertTrue(
            AuditLog.objects.filter(
                object_type="Incident",
                object_id=incident.id,
                action=AuditLog.ACTION_APPROVE,
            ).exists()
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_staff_user_can_add_internal_note_from_custom_admin(self):
        incident = Incident.objects.create(
            title="Comment Update",
            category="other",
            description="Needs internal note",
            incident_date=date(2026, 3, 1),
            created_by=self.user,
        )

        self.client.login(username="adminuser", password="pass12345")
        response = self.client.post(
            reverse("admin:incident_comment", args=[incident.id]),
            {"comment": "Follow up with the reporting team."},
        )

        self.assertEqual(response.status_code, 302)
        note = IncidentComment.objects.get(incident=incident)
        self.assertEqual(note.created_by, self.staff_user)
        self.assertTrue(note.is_admin_note)
        self.assertTrue(
            AuditLog.objects.filter(
                object_type="Incident",
                object_id=incident.id,
                message__icontains="Admin note added",
            ).exists()
        )

    def test_manager_can_open_staff_accounts_page(self):
        self.client.login(username="systemadmin40329", password="pass12345")
        response = self.client.get(reverse("admin:staff_accounts"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "incidents/admin_staff_accounts.html")
        self.assertContains(response, "Create New Staff User")

    def test_regular_staff_cannot_open_staff_accounts_page(self):
        self.client.login(username="adminuser", password="pass12345")
        response = self.client.get(reverse("admin:staff_accounts"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("admin:index"))

    def test_manager_can_create_staff_user_from_staff_accounts_page(self):
        self.client.login(username="systemadmin40329", password="pass12345")
        response = self.client.post(
            reverse("admin:staff_accounts"),
            {
                "action": "create_staff",
                "create-full_name": "Staff Person",
                "create-email": "staffperson@example.com",
                "create-password1": "StrongPass123!",
                "create-password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        created_user = User.objects.get(email="staffperson@example.com")
        self.assertTrue(created_user.is_staff)
        self.assertFalse(created_user.is_superuser)

    def test_manager_can_promote_existing_user_to_staff(self):
        existing_user = User.objects.create_user(
            username="existinguser",
            email="existing@example.com",
            password="pass12345",
        )

        self.client.login(username="systemadmin40329", password="pass12345")
        response = self.client.post(
            reverse("admin:staff_accounts"),
            {
                "action": "promote_staff",
                "promote-user": existing_user.id,
            },
        )

        self.assertEqual(response.status_code, 302)
        existing_user.refresh_from_db()
        self.assertTrue(existing_user.is_staff)
        self.assertFalse(existing_user.is_superuser)


class AdminSetupTests(TestCase):
    def test_admin_setup_creates_first_admin_when_no_staff_exists(self):
        response = self.client.post(
            reverse("admin:setup"),
            {
                "full_name": "First Admin",
                "email": "firstadmin@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("admin:index"))
        created_user = User.objects.get(email="firstadmin@example.com")
        self.assertTrue(created_user.is_staff)
        self.assertTrue(created_user.is_superuser)

    def test_admin_index_redirects_to_setup_when_no_staff_exists(self):
        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("admin:setup"))

    def test_admin_setup_redirects_to_login_when_staff_already_exists(self):
        User.objects.create_user(
            username="systemadmin40329",
            email="manager@example.com",
            password="pass12345",
            is_staff=True,
            is_superuser=True,
        )

        response = self.client.get(reverse("admin:setup"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:staff_login"))

    def test_admin_dashboard_redirects_unauthenticated_user_to_staff_login(self):
        User.objects.create_user(
            username="systemadmin40329",
            email="manager@example.com",
            password="pass12345",
            is_staff=True,
            is_superuser=True,
        )

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:staff_login"), response.url)
