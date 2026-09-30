from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()
STRONG = "Str0ng!Passw0rd"


class AuthTests(APITestCase):
    def register(self, **over):
        data = {"username": "alice", "email": "alice@example.com",
                "password": STRONG, "password2": STRONG}
        data.update(over)
        return self.client.post("/api/auth/register/", data, format="json")

    def login(self):
        return self.client.post("/api/auth/login/", {"username": "alice", "password": STRONG}, format="json")

    def test_register_success_and_password_hashed(self):
        r = self.register()
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", r.data)
        user = User.objects.get(username="alice")
        self.assertNotEqual(user.password, STRONG)
        self.assertTrue(user.password.startswith("pbkdf2_sha256$"))

    def test_register_password_mismatch(self):
        r = self.register(password2="different")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password(self):
        r = self.register(password="12345678", password2="12345678")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        self.register()
        r = self.register(username="bob")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_jwt(self):
        self.register()
        r = self.login()
        self.assertEqual(r.status_code, 200)
        self.assertIn("access", r.data)
        self.assertIn("refresh", r.data)

    def test_login_wrong_password(self):
        self.register()
        r = self.client.post("/api/auth/login/", {"username": "alice", "password": "nope"}, format="json")
        self.assertEqual(r.status_code, 401)

    def test_protected_route_requires_token(self):
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 401)

    def test_protected_route_with_token(self):
        self.register()
        tokens = self.login().data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        r = self.client.get("/api/auth/me/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["username"], "alice")

    def test_logout_blacklists_refresh_token(self):
        self.register()
        tokens = self.login().data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        r = self.client.post("/api/auth/logout/", {"refresh": tokens["refresh"]}, format="json")
        self.assertEqual(r.status_code, 205)
        r2 = self.client.post("/api/auth/refresh/", {"refresh": tokens["refresh"]}, format="json")
        self.assertEqual(r2.status_code, 401)
