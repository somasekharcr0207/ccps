from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user stored in the `users` table. Password is hashed (PBKDF2-SHA256)."""
    email = models.EmailField(unique=True)

    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.username
