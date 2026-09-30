import re
from datetime import date

from rest_framework import serializers

from .models import Card
from .utils import detect_brand, luhn_valid, mask_number


class CardCreateSerializer(serializers.ModelSerializer):
    """card_number and cvv are write-only, validated, and DISCARDED (never persisted)."""
    card_number = serializers.CharField(write_only=True)
    cvv = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = Card
        fields = ("id", "card_holder_name", "card_type", "card_number", "cvv", "expiry_month",
                  "expiry_year", "brand", "masked_number", "last4", "created_at")
        read_only_fields = ("id", "brand", "masked_number", "last4", "created_at")

    def validate_card_holder_name(self, value):
        value = value.strip()
        if not re.fullmatch(r"[A-Za-z][A-Za-z .'-]{1,99}", value):
            raise serializers.ValidationError("Enter a valid card holder name.")
        return value

    def validate_card_number(self, value):
        number = re.sub(r"[\s-]", "", value)
        if not number.isdigit() or not 13 <= len(number) <= 19:
            raise serializers.ValidationError("Card number must be 13-19 digits.")
        if not luhn_valid(number):
            raise serializers.ValidationError("Invalid card number.")
        return number

    def validate_cvv(self, value):
        if value and not re.fullmatch(r"\d{3,4}", value):
            raise serializers.ValidationError("CVV must be 3 or 4 digits.")
        return value

    def validate_expiry_month(self, value):
        if not 1 <= value <= 12:
            raise serializers.ValidationError("Month must be between 1 and 12.")
        return value

    def validate(self, attrs):
        today = date.today()
        y, m = attrs["expiry_year"], attrs["expiry_month"]
        if y < 100:
            y += 2000
            attrs["expiry_year"] = y
        if (y, m) < (today.year, today.month):
            raise serializers.ValidationError({"expiry_year": "Card has expired."})
        if y > today.year + 20:
            raise serializers.ValidationError({"expiry_year": "Invalid expiry year."})
        return attrs

    def create(self, validated_data):
        number = validated_data.pop("card_number")
        validated_data.pop("cvv", None)  # never stored
        card = Card.objects.create(
            brand=detect_brand(number),
            masked_number=mask_number(number),
            last4=number[-4:],
            **validated_data,
        )
        return card


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ("id", "card_holder_name", "card_type", "brand", "masked_number", "last4",
                  "expiry_month", "expiry_year", "created_at")
        read_only_fields = fields
