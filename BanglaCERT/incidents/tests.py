from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Incident, IncidentComment


User = get_user_model()


class IncidentWorkflowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="normaluser", password="pass12345")
        self.other_user = User.objects.create_user(username="otheruser", password="pass12345")
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
            reverse("incidents:report"),
            {
                "title": "Anonymous Email Scam",
                "category": "phishing",
                "description": "Guest submitted phishing report.",
                "incident_date": "2026-03-02",
                "reporter_email": "guest@example.com",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("incidents:report_success"))
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

    def test_staff_user_redirected_to_django_admin_from_user_portal(self):
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
