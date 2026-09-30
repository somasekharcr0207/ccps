import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Create the demo admin and demo user (passwords from env, never hard-coded in the DB)."

    def handle(self, *args, **options):
        admin_pw = os.getenv("ADMIN_PASSWORD", "Admin@12345")
        user_pw = os.getenv("DEMO_USER_PASSWORD", "Demo@12345")
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", admin_pw)
            self.stdout.write(self.style.SUCCESS("Created admin"))
        if not User.objects.filter(username="demo").exists():
            User.objects.create_user("demo", "demo@example.com", user_pw, first_name="Demo", last_name="User")
            self.stdout.write(self.style.SUCCESS("Created demo user"))
