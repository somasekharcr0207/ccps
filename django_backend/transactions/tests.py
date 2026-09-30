from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from adminpanel.models import AdminLog
from cards.models import Card

from .models import Transaction

User = get_user_model()


class TransactionTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", "a@example.com", "Str0ng!Passw0rd")
        self.other = User.objects.create_user("bob", "b@example.com", "Str0ng!Passw0rd")
        self.admin = User.objects.create_superuser("admin", "admin@example.com", "Adm1n!Passw0rd")
        self.card = Card.objects.create(user=self.user, card_holder_name="Alice", card_type="CREDIT",
                                        brand="VISA", masked_number="**** **** **** 1111", last4="1111",
                                        expiry_month=12, expiry_year=2035)
        self.t1 = Transaction.objects.create(user=self.user, card=self.card, amount=Decimal("100.00"),
                                             status="SUCCESS")
        self.t2 = Transaction.objects.create(user=self.user, card=self.card, amount=Decimal("500.00"),
                                             status="FAILED", failure_reason="Declined")
        Transaction.objects.create(user=self.other, amount=Decimal("999.00"), status="SUCCESS")
        old = Transaction.objects.create(user=self.user, amount=Decimal("50.00"), status="PENDING")
        Transaction.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=10))
        self.old = old

    def test_only_own_transactions(self):
        self.client.force_authenticate(self.user)
        r = self.client.get("/api/transactions/")
        self.assertEqual(r.data["count"], 3)

    def test_filter_status(self):
        self.client.force_authenticate(self.user)
        r = self.client.get("/api/transactions/?status=FAILED")
        self.assertEqual(r.data["count"], 1)

    def test_filter_amount(self):
        self.client.force_authenticate(self.user)
        r = self.client.get("/api/transactions/?min_amount=100&max_amount=200")
        self.assertEqual(r.data["count"], 1)

    def test_filter_date(self):
        self.client.force_authenticate(self.user)
        start = (timezone.now() - timedelta(days=2)).date().isoformat()
        r = self.client.get(f"/api/transactions/?date_from={start}")
        self.assertEqual(r.data["count"], 2)

    def test_cannot_view_other_users_transaction(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/transactions/{self.t1.pk}/").status_code, 404)

    def test_export_forbidden_for_normal_user(self):
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get("/api/transactions/admin/export/").status_code, 403)

    def test_admin_export_csv_and_logged(self):
        self.client.force_authenticate(self.admin)
        r = self.client.get("/api/transactions/admin/export/?status=SUCCESS")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "text/csv")
        lines = r.content.decode().strip().splitlines()
        self.assertEqual(len(lines), 3)  # header + 2 SUCCESS
        self.assertTrue(AdminLog.objects.filter(action="EXPORT_CSV").exists())
