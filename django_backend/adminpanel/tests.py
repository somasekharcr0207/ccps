from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from transactions.models import Transaction

from .models import AdminLog

User = get_user_model()


class AdminPanelTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", "a@example.com", "Str0ng!Passw0rd")
        self.admin = User.objects.create_superuser("admin", "admin@example.com", "Adm1n!Passw0rd")
        Transaction.objects.create(user=self.user, amount=Decimal("100"), status="SUCCESS")
        Transaction.objects.create(user=self.user, amount=Decimal("40"), status="SUCCESS")
        Transaction.objects.create(user=self.user, amount=Decimal("70"), status="FAILED")

    def test_non_admin_forbidden(self):
        self.client.force_authenticate(self.user)
        for url in ("users/", "cards/", "transactions/", "daily-summary/", "logs/"):
            self.assertEqual(self.client.get(f"/api/admin/{url}").status_code, 403, url)

    def test_admin_lists(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get("/api/admin/users/").data["count"], 2)
        self.assertEqual(self.client.get("/api/admin/transactions/").data["count"], 3)

    def test_daily_summary(self):
        self.client.force_authenticate(self.admin)
        r = self.client.get("/api/admin/daily-summary/")
        self.assertEqual(r.status_code, 200)
        row = r.data[0]
        self.assertEqual(row["total_transactions"], 3)
        self.assertEqual(row["success_count"], 2)
        self.assertEqual(row["failed_count"], 1)
        self.assertEqual(Decimal(str(row["total_success_amount"])), Decimal("140"))

    def test_deactivate_user_is_logged(self):
        self.client.force_authenticate(self.admin)
        r = self.client.patch(f"/api/admin/users/{self.user.pk}/", {"is_active": False}, format="json")
        self.assertEqual(r.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertTrue(AdminLog.objects.filter(action="USER_DEACTIVATED").exists())

    def test_bad_date_param(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get("/api/admin/daily-summary/?date_from=abc").status_code, 400)
