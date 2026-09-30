from django.conf import settings
from django.db import models


class Card(models.Model):
    """Only masked number + last 4 digits are stored. No PAN, no CVV - ever."""

    class Brand(models.TextChoices):
        VISA = "VISA", "Visa"
        MASTERCARD = "MASTERCARD", "Mastercard"
        AMEX = "AMEX", "American Express"
        DISCOVER = "DISCOVER", "Discover"
        RUPAY = "RUPAY", "RuPay"
        OTHER = "OTHER", "Other"

    class CardType(models.TextChoices):
        CREDIT = "CREDIT", "Credit"
        DEBIT = "DEBIT", "Debit"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cards")
    card_holder_name = models.CharField(max_length=100)
    card_type = models.CharField(max_length=6, choices=CardType.choices)
    brand = models.CharField(max_length=12, choices=Brand.choices, default=Brand.OTHER)
    masked_number = models.CharField(max_length=25)  # e.g. **** **** **** 1111
    last4 = models.CharField(max_length=4)
    expiry_month = models.PositiveSmallIntegerField()
    expiry_year = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cards"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "last4"])]

    def __str__(self):
        return f"{self.brand} {self.masked_number}"
