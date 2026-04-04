from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from incidents.models import Incident


User = get_user_model()


class SearchFeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="searcher", password="pass12345")
        self.phishing_incident = Incident.objects.create(
            title="Credential theft against alice@example.com",
            category="phishing",
            description="Victim received a fake login form and visited https://secret.example.com.",
            incident_date=date(2026, 3, 1),
            status=Incident.STATUS_VERIFIED,
            created_by=self.user,
        )
        self.malware_incident = Incident.objects.create(
            title="Malware campaign",
            category="malware",
            description="Public malware awareness content.",
            incident_date=date(2026, 3, 15),
            status=Incident.STATUS_VERIFIED,
            created_by=self.user,
        )
        self.pending_incident = Incident.objects.create(
            title="Pending fraud report",
            category="fraud",
            description="Should stay out of public search.",
            incident_date=date(2026, 3, 20),
            status=Incident.STATUS_PENDING,
            created_by=self.user,
        )

    def test_search_page_shows_only_verified_and_masked_incidents(self):
        response = self.client.get(reverse("incidents:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Credential theft against [hidden email]")
        self.assertContains(response, "[hidden link]")
        self.assertNotContains(response, "alice@example.com")
        self.assertNotContains(response, "Pending fraud report")

    def test_search_filters_by_category_date_and_keyword(self):
        response = self.client.get(
            reverse("incidents:home"),
            {
                "q": "malware",
                "category": "malware",
                "date_from": "2026-03-10",
                "date_to": "2026-03-31",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Malware campaign")
        self.assertNotContains(response, "Credential theft")

    def test_search_index_redirects_to_home_section(self):
        response = self.client.get(reverse("search:index"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"{reverse('incidents:home')}#awareness")

    def test_search_ajax_returns_filtered_partial(self):
        response = self.client.get(
            reverse("search:index"),
            {"category": "phishing"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Credential theft against [hidden email]")
        self.assertNotContains(response, "<!doctype html>")
