from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from incidents.models import Incident


User = get_user_model()


class AnalyticsDashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="analyst", password="pass12345")
        Incident.objects.create(
            title="Phishing case",
            category="phishing",
            description="One phishing report.",
            incident_date=date(2026, 1, 5),
            status=Incident.STATUS_VERIFIED,
            created_by=self.user,
        )
        Incident.objects.create(
            title="Malware case",
            category="malware",
            description="One malware report.",
            incident_date=date(2026, 2, 10),
            status=Incident.STATUS_PENDING,
            created_by=self.user,
        )
        Incident.objects.create(
            title="Second phishing case",
            category="phishing",
            description="Another phishing report.",
            incident_date=date(2026, 2, 18),
            status=Incident.STATUS_VERIFIED,
            created_by=self.user,
        )

    def test_dashboard_shows_summary_cards_and_category_chart(self):
        response = self.client.get(reverse("incidents:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verified Posts Analyzed")
        self.assertContains(response, "Verified Incidents")
        self.assertContains(response, "<h2 style=\"margin: 0;\">2</h2>", html=True)
        self.assertNotContains(response, "Malware case")
        self.assertContains(response, "Most Common Attack")
        self.assertContains(response, "Phishing")

    def test_dashboard_shows_frequency_graph_labels(self):
        response = self.client.get(reverse("incidents:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jan 2026")
        self.assertContains(response, "Feb 2026")
        self.assertContains(response, "Incident Frequency Graph")

    def test_analytics_index_redirects_to_home_section(self):
        response = self.client.get(reverse("analytics:dashboard"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"{reverse('incidents:home')}#analytics")
