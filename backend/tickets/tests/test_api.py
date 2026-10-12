from django.urls import reverse
from rest_framework import status as http
from rest_framework.test import APITestCase

from tickets.models import Ticket


def make_ticket(**overrides):
    data = {"title": "Something broke"} | overrides
    return Ticket.objects.create(**data)


class CreateTicketTests(APITestCase):
    url = "/tickets"

    def test_creates_ticket_with_defaults(self):
        res = self.client.post(self.url, {"title": "Cannot log in"}, format="json")

        self.assertEqual(res.status_code, http.HTTP_201_CREATED)
        self.assertEqual(res.data["status"], "open")
        self.assertEqual(res.data["priority"], "medium")
        self.assertEqual(res.data["description"], "")
        self.assertIsNotNone(res.data["created_at"])
        self.assertEqual(Ticket.objects.count(), 1)

    def test_accepts_explicit_priority_description_and_trims_title(self):
        res = self.client.post(
            self.url,
            {"title": "  Disk full  ", "description": "db01 at 98%", "priority": "high"},
            format="json",
        )

        self.assertEqual(res.status_code, http.HTTP_201_CREATED)
        self.assertEqual(res.data["title"], "Disk full")
        self.assertEqual(res.data["priority"], "high")

    def test_rejects_missing_or_blank_title(self):
        for payload in ({}, {"title": ""}, {"title": "   "}):
            with self.subTest(payload=payload):
                res = self.client.post(self.url, payload, format="json")
                self.assertEqual(res.status_code, http.HTTP_400_BAD_REQUEST)
                self.assertIn("title", res.data)
        self.assertEqual(Ticket.objects.count(), 0)

    def test_rejects_invalid_enum_values(self):
        for field in ("status", "priority"):
            with self.subTest(field=field):
                res = self.client.post(self.url, {"title": "x", field: "urgent"}, format="json")
                self.assertEqual(res.status_code, http.HTTP_400_BAD_REQUEST)
                self.assertIn(field, res.data)

    def test_client_cannot_set_id_or_created_at(self):
        res = self.client.post(
            self.url, {"title": "x", "id": 999, "created_at": "2000-01-01T00:00:00Z"}, format="json"
        )

        self.assertEqual(res.status_code, http.HTTP_201_CREATED)
        self.assertNotEqual(res.data["id"], 999)
        self.assertNotEqual(res.data["created_at"], "2000-01-01T00:00:00Z")


class ListTicketTests(APITestCase):
    url = "/tickets"

    def test_empty_list_has_pagination_envelope(self):
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, http.HTTP_200_OK)
        self.assertEqual(res.data["count"], 0)
        self.assertEqual(res.data["results"], [])

    def test_lists_newest_first(self):
        first, second = make_ticket(title="first"), make_ticket(title="second")

        res = self.client.get(self.url)

        self.assertEqual([t["id"] for t in res.data["results"]], [second.id, first.id])

    def test_filters_by_status(self):
        make_ticket(status=Ticket.Status.OPEN)
        done = make_ticket(status=Ticket.Status.CLOSED)

        res = self.client.get(self.url, {"status": "closed"})

        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["id"], done.id)

    def test_invalid_status_filter_is_a_400(self):
        res = self.client.get(self.url, {"status": "nope"})

        self.assertEqual(res.status_code, http.HTTP_400_BAD_REQUEST)

    def test_paginates_with_page_and_limit(self):
        tickets = [make_ticket(title=f"t{i}") for i in range(5)]
        newest_first = [t.id for t in reversed(tickets)]

        page1 = self.client.get(self.url, {"page": 1, "limit": 2})
        page3 = self.client.get(self.url, {"page": 3, "limit": 2})

        self.assertEqual(page1.data["count"], 5)
        self.assertEqual([t["id"] for t in page1.data["results"]], newest_first[:2])
        self.assertIsNotNone(page1.data["next"])
        self.assertEqual([t["id"] for t in page3.data["results"]], newest_first[4:])
        self.assertIsNone(page3.data["next"])

    def test_limit_is_capped_and_out_of_range_page_is_404(self):
        for i in range(3):
            make_ticket(title=f"t{i}")

        capped = self.client.get(self.url, {"limit": 100000})
        beyond = self.client.get(self.url, {"page": 9})

        self.assertEqual(capped.status_code, http.HTTP_200_OK)
        self.assertEqual(beyond.status_code, http.HTTP_404_NOT_FOUND)

    def test_status_filter_composes_with_pagination(self):
        for i in range(3):
            make_ticket(title=f"open{i}")
        make_ticket(title="closed", status=Ticket.Status.CLOSED)

        res = self.client.get(self.url, {"status": "open", "limit": 2})

        self.assertEqual(res.data["count"], 3)
        self.assertEqual(len(res.data["results"]), 2)


class UpdateTicketTests(APITestCase):
    def url(self, pk):
        return f"/tickets/{pk}"

    def test_updates_status_and_returns_full_ticket(self):
        ticket = make_ticket()

        res = self.client.patch(self.url(ticket.id), {"status": "in_progress"}, format="json")

        self.assertEqual(res.status_code, http.HTTP_200_OK)
        self.assertEqual(res.data["status"], "in_progress")
        self.assertEqual(res.data["title"], ticket.title)
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, Ticket.Status.IN_PROGRESS)

    def test_updates_priority(self):
        ticket = make_ticket()

        res = self.client.patch(self.url(ticket.id), {"priority": "low"}, format="json")

        self.assertEqual(res.status_code, http.HTTP_200_OK)
        self.assertEqual(res.data["priority"], "low")

    def test_rejects_invalid_value_unknown_field_and_empty_body(self):
        ticket = make_ticket()
        for payload in ({"status": "done"}, {"title": "renamed"}, {}):
            with self.subTest(payload=payload):
                res = self.client.patch(self.url(ticket.id), payload, format="json")
                self.assertEqual(res.status_code, http.HTTP_400_BAD_REQUEST)
        ticket.refresh_from_db()
        self.assertEqual(ticket.title, "Something broke")
        self.assertEqual(ticket.status, Ticket.Status.OPEN)

    def test_missing_ticket_is_404(self):
        res = self.client.patch(self.url(12345), {"status": "closed"}, format="json")

        self.assertEqual(res.status_code, http.HTTP_404_NOT_FOUND)

    def test_put_and_delete_are_not_allowed(self):
        ticket = make_ticket()

        self.assertEqual(self.client.put(self.url(ticket.id), {}, format="json").status_code, 405)
        self.assertEqual(self.client.delete(self.url(ticket.id)).status_code, 405)


class StatsTests(APITestCase):
    url = "/tickets/stats"

    def test_all_statuses_are_zero_when_empty(self):
        res = self.client.get(self.url)

        self.assertEqual(res.status_code, http.HTTP_200_OK)
        self.assertEqual(res.data, {"open": 0, "in_progress": 0, "closed": 0})

    def test_counts_tickets_grouped_by_status(self):
        for _ in range(2):
            make_ticket(status=Ticket.Status.OPEN)
        make_ticket(status=Ticket.Status.IN_PROGRESS)
        for _ in range(3):
            make_ticket(status=Ticket.Status.CLOSED)

        res = self.client.get(self.url)

        self.assertEqual(res.data, {"open": 2, "in_progress": 1, "closed": 3})

    def test_stats_reflect_status_changes(self):
        ticket = make_ticket()
        self.client.patch(f"/tickets/{ticket.id}", {"status": "closed"}, format="json")

        res = self.client.get(self.url)

        self.assertEqual(res.data, {"open": 0, "in_progress": 0, "closed": 1})


class HealthTests(APITestCase):
    def test_health_checks_database(self):
        res = self.client.get(reverse("health"))

        self.assertEqual(res.status_code, http.HTTP_200_OK)
        self.assertEqual(res.json(), {"status": "ok"})
