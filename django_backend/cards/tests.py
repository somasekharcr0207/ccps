from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from .models import Card
from .utils import luhn_valid

User = get_user_model()
VALID = "4111 1111 1111 1111"


def payload(**over):
    data = {"card_holder_name": "Alice Doe", "card_type": "CREDIT", "card_number": VALID,
            "cvv": "123", "expiry_month": 12, "expiry_year": 2035}
    data.update(over)
    return data


class CardTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", "a@example.com", "Str0ng!Passw0rd")
        self.other = User.objects.create_user("bob", "b@example.com", "Str0ng!Passw0rd")
        self.client.force_authenticate(self.user)

    def test_luhn(self):
        self.assertTrue(luhn_valid("4111111111111111"))
        self.assertFalse(luhn_valid("4111111111111112"))

    def test_add_card_stores_only_masked_and_last4(self):
        r = self.client.post("/api/cards/", payload(), format="json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.data["last4"], "1111")
        self.assertEqual(r.data["masked_number"], "**** **** **** 1111")
        self.assertNotIn("card_number", r.data)
        self.assertNotIn("cvv", r.data)
        card = Card.objects.get()
        stored = " ".join(str(getattr(card, f.name)) for f in Card._meta.fields)
        self.assertNotIn("41111111111111", stored)
        self.assertFalse(any("cvv" in f.name.lower() for f in Card._meta.fields))

    def test_invalid_card_number_rejected(self):
        r = self.client.post("/api/cards/", payload(card_number="4111111111111112"), format="json")
        self.assertEqual(r.status_code, 400)

    def test_expired_card_rejected(self):
        r = self.client.post("/api/cards/", payload(expiry_year=2020), format="json")
        self.assertEqual(r.status_code, 400)

    def test_bad_cvv_rejected(self):
        r = self.client.post("/api/cards/", payload(cvv="12"), format="json")
        self.assertEqual(r.status_code, 400)

    def test_list_only_own_cards(self):
        self.client.post("/api/cards/", payload(), format="json")
        self.client.force_authenticate(self.other)
        r = self.client.get("/api/cards/")
        self.assertEqual(r.data["count"], 0)

    def test_delete_own_card(self):
        cid = self.client.post("/api/cards/", payload(), format="json").data["id"]
        self.assertEqual(self.client.delete(f"/api/cards/{cid}/").status_code, 204)
        self.assertEqual(Card.objects.count(), 0)

    def test_cannot_delete_other_users_card(self):
        cid = self.client.post("/api/cards/", payload(), format="json").data["id"]
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.delete(f"/api/cards/{cid}/").status_code, 404)
        self.assertEqual(Card.objects.count(), 1)

    def test_requires_auth(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/cards/").status_code, 401)
