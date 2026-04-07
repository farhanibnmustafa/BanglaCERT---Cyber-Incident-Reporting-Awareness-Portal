from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from incidents.models import Incident

from .models import AwarenessComment, AwarenessLike, AwarenessShare


User = get_user_model()


class AwarenessFeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reader", email="reader@example.com", password="pass12345")
        self.staff_user = User.objects.create_user(
            username="staffer",
            email="staffer@example.com",
            password="pass12345",
            is_staff=True,
        )
        self.verified_incident = Incident.objects.create(
            title="Verified Phishing Case reported by victim@example.com",
            category="phishing",
            description="A verified phishing incident was published for public awareness. Contact +8801712345678 or visit https://private.example.com for internal follow-up.",
            incident_date=date(2026, 3, 10),
            status=Incident.STATUS_VERIFIED,
            created_by=self.user,
        )
        self.pending_incident = Incident.objects.create(
            title="Pending Case",
            category="fraud",
            description="This should not appear publicly.",
            incident_date=date(2026, 3, 11),
            status=Incident.STATUS_PENDING,
            created_by=self.user,
        )

    def test_awareness_list_shows_only_verified_incidents(self):
        response = self.client.get(reverse("incidents:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verified Phishing Case")
        self.assertNotContains(response, "Pending Case")

    def test_awareness_index_renders_verified_posts_page(self):
        response = self.client.get(reverse("awareness:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verified Phishing Case")
        self.assertNotContains(response, "Pending Case")
        self.assertContains(response, 'class="story-grid"')

    def test_staff_user_can_access_verified_posts_page(self):
        self.client.login(username="staffer", password="pass12345")

        response = self.client.get(reverse("awareness:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Verified Phishing Case")
        self.assertContains(response, 'class="react-post-root"')

    def test_public_awareness_view_masks_confidential_data(self):
        response = self.client.get(reverse("awareness:detail", args=[self.verified_incident.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "[hidden email]")
        self.assertContains(response, "[hidden phone]")
        self.assertContains(response, "[hidden link]")
        self.assertNotContains(response, "victim@example.com")
        self.assertNotContains(response, "https://private.example.com")

    def test_logged_in_user_can_like_and_unlike_verified_post(self):
        self.client.login(username="reader", password="pass12345")

        like_response = self.client.post(reverse("awareness:toggle_like", args=[self.verified_incident.id]))
        unlike_response = self.client.post(reverse("awareness:toggle_like", args=[self.verified_incident.id]))

        self.assertEqual(like_response.status_code, 302)
        self.assertEqual(unlike_response.status_code, 302)
        self.assertEqual(AwarenessLike.objects.filter(incident=self.verified_incident, created_by=self.user).count(), 0)

    def test_like_redirect_honors_next_anchor(self):
        self.client.login(username="reader", password="pass12345")

        response = self.client.post(
            reverse("awareness:toggle_like", args=[self.verified_incident.id]),
            {"next": "/incidents/#awareness"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/incidents/#awareness")

    def test_staff_user_can_like_verified_post(self):
        self.client.login(username="staffer", password="pass12345")

        response = self.client.post(
            reverse("awareness:toggle_like", args=[self.verified_incident.id]),
            {"next": reverse("awareness:list")},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("awareness:list"))
        self.assertTrue(
            AwarenessLike.objects.filter(
                incident=self.verified_incident,
                created_by=self.staff_user,
            ).exists()
        )

    def test_logged_in_user_can_comment_on_verified_post_with_timestamp(self):
        self.client.login(username="reader", password="pass12345")

        response = self.client.post(
            reverse("awareness:add_comment", args=[self.verified_incident.id]),
            {"comment": "This awareness post is helpful."},
        )

        self.assertEqual(response.status_code, 302)
        comment = AwarenessComment.objects.get(incident=self.verified_incident)
        self.assertEqual(comment.created_by, self.user)
        self.assertIsNotNone(comment.created_at)
        detail_response = self.client.get(reverse("awareness:detail", args=[self.verified_incident.id]))
        self.assertContains(detail_response, "This awareness post is helpful.")

    def test_staff_user_can_comment_on_verified_post(self):
        self.client.login(username="staffer", password="pass12345")

        response = self.client.post(
            reverse("awareness:add_comment", args=[self.verified_incident.id]),
            {"comment": "Admin review note for public readers."},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            AwarenessComment.objects.filter(
                incident=self.verified_incident,
                created_by=self.staff_user,
                comment="Admin review note for public readers.",
            ).exists()
        )

    def test_verified_post_can_be_shared(self):
        response = self.client.post(
            reverse("awareness:share", args=[self.verified_incident.id]),
            {"next": "/incidents/#awareness"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/incidents/#awareness")
        self.assertEqual(AwarenessShare.objects.filter(incident=self.verified_incident).count(), 1)

    def test_unverified_post_cannot_be_shared(self):
        response = self.client.post(reverse("awareness:share", args=[self.pending_incident.id]))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(AwarenessShare.objects.filter(incident=self.pending_incident).count(), 0)
