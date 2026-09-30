from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import AdminLog

User = get_user_model()


class AdminUserSerializer(serializers.ModelSerializer):
    card_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "is_active", "is_staff",
                  "date_joined", "last_login", "card_count")
        read_only_fields = ("id", "username", "email", "first_name", "last_name", "is_staff",
                            "date_joined", "last_login", "card_count")


class AdminCardSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField(source="user.username")
    card_holder_name = serializers.CharField()
    card_type = serializers.CharField()
    brand = serializers.CharField()
    masked_number = serializers.CharField()
    last4 = serializers.CharField()
    expiry_month = serializers.IntegerField()
    expiry_year = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class AdminLogSerializer(serializers.ModelSerializer):
    admin = serializers.CharField(source="admin.username", default=None)

    class Meta:
        model = AdminLog
        fields = ("id", "admin", "action", "details", "created_at")


class DailySummarySerializer(serializers.Serializer):
    date = serializers.DateField()
    total_transactions = serializers.IntegerField()
    success_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    total_success_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
