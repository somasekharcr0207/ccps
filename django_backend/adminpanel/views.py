from datetime import date

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from cards.models import Card
from transactions.filters import TransactionFilter
from transactions.models import Transaction
from transactions.serializers import TransactionSerializer

from .models import AdminLog
from .serializers import (AdminCardSerializer, AdminLogSerializer, AdminUserSerializer,
                          DailySummarySerializer)

User = get_user_model()


class AdminOnly:
    permission_classes = (permissions.IsAdminUser,)


class AdminUserListView(AdminOnly, generics.ListAPIView):
    serializer_class = AdminUserSerializer
    queryset = User.objects.annotate(card_count=Count("cards")).order_by("-date_joined")
    filterset_fields = ("is_active", "is_staff")


class AdminUserDetailView(AdminOnly, generics.RetrieveUpdateAPIView):
    """PATCH {"is_active": false} to block a user."""
    serializer_class = AdminUserSerializer
    queryset = User.objects.annotate(card_count=Count("cards"))
    http_method_names = ["get", "patch", "head", "options"]

    def perform_update(self, serializer):
        was_active = serializer.instance.is_active
        user = serializer.save()
        if was_active != user.is_active:
            AdminLog.objects.create(
                admin=self.request.user,
                action=AdminLog.Action.USER_ACTIVATED if user.is_active else AdminLog.Action.USER_DEACTIVATED,
                details=f"user_id={user.id} username={user.username}")


class AdminCardListView(AdminOnly, generics.ListAPIView):
    serializer_class = AdminCardSerializer
    queryset = Card.objects.select_related("user").order_by("-created_at")
    filterset_fields = ("user", "brand", "card_type")


class AdminTransactionListView(AdminOnly, generics.ListAPIView):
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.select_related("user", "card").order_by("-created_at")
    filterset_class = TransactionFilter


class AdminLogListView(AdminOnly, generics.ListAPIView):
    serializer_class = AdminLogSerializer
    queryset = AdminLog.objects.select_related("admin")
    filterset_fields = ("action",)


class DailySummaryView(AdminOnly, APIView):
    @extend_schema(
        parameters=[OpenApiParameter("date_from", str), OpenApiParameter("date_to", str)],
        responses=DailySummarySerializer(many=True))
    def get(self, request):
        qs = Transaction.objects.all()
        try:
            if request.query_params.get("date_from"):
                qs = qs.filter(created_at__date__gte=date.fromisoformat(request.query_params["date_from"]))
            if request.query_params.get("date_to"):
                qs = qs.filter(created_at__date__lte=date.fromisoformat(request.query_params["date_to"]))
        except ValueError:
            return Response({"detail": "Dates must be YYYY-MM-DD."}, status=400)
        rows = (qs.annotate(date=TruncDate("created_at")).values("date").annotate(
            total_transactions=Count("id"),
            success_count=Count("id", filter=Q(status="SUCCESS")),
            failed_count=Count("id", filter=Q(status="FAILED")),
            pending_count=Count("id", filter=Q(status="PENDING")),
            total_success_amount=Sum("amount", filter=Q(status="SUCCESS")),
        ).order_by("-date"))
        data = [{**r, "total_success_amount": r["total_success_amount"] or 0} for r in rows]
        AdminLog.objects.create(admin=request.user, action=AdminLog.Action.VIEW_SUMMARY,
                                details=f"params={dict(request.query_params)}")
        return Response(DailySummarySerializer(data, many=True).data)
