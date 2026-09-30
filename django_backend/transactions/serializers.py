from rest_framework import serializers

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    card_last4 = serializers.CharField(source="card.last4", read_only=True, default=None)
    card_brand = serializers.CharField(source="card.brand", read_only=True, default=None)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Transaction
        fields = ("id", "reference", "username", "card", "card_last4", "card_brand", "amount",
                  "currency", "description", "status", "failure_reason", "created_at", "updated_at")
        read_only_fields = fields
