import csv

from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.views import APIView

from adminpanel.models import AdminLog

from .filters import TransactionFilter
from .models import Transaction
from .serializers import TransactionSerializer


def _csv_safe(value):
    """Neutralise spreadsheet formula injection."""
    s = "" if value is None else str(value)
    return "'" + s if s[:1] in ("=", "+", "-", "@") else s


class TransactionListView(generics.ListAPIView):
    """User's own history. Filters: date_from, date_to, min_amount, max_amount, status."""
    serializer_class = TransactionSerializer
    filterset_class = TransactionFilter

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).select_related("card", "user")


class TransactionDetailView(generics.RetrieveAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user).select_related("card", "user")


class AdminTransactionExportView(APIView):
    """Admin only: CSV export honouring the same filters."""
    permission_classes = (permissions.IsAdminUser,)
    filterset_class = TransactionFilter

    def get(self, request):
        qs = Transaction.objects.select_related("card", "user").order_by("-created_at")
        qs = TransactionFilter(request.query_params, queryset=qs).qs
        stamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="transactions_{stamp}.csv"'
        writer = csv.writer(response)
        writer.writerow(["reference", "username", "card_last4", "amount", "currency",
                         "status", "failure_reason", "description", "created_at"])
        count = 0
        for t in qs.iterator():
            writer.writerow([t.reference, _csv_safe(t.user.username), t.card.last4 if t.card else "",
                             t.amount, t.currency, t.status, _csv_safe(t.failure_reason),
                             _csv_safe(t.description), t.created_at.isoformat()])
            count += 1
        AdminLog.objects.create(admin=request.user, action=AdminLog.Action.EXPORT_CSV,
                                details=f"Exported {count} transactions; filters={dict(request.query_params)}")
        return response
