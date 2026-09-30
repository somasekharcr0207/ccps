from django.urls import path

from .views import AdminTransactionExportView, TransactionDetailView, TransactionListView

urlpatterns = [
    path("", TransactionListView.as_view(), name="transaction-list"),
    path("admin/export/", AdminTransactionExportView.as_view(), name="transaction-export"),
    path("<int:pk>/", TransactionDetailView.as_view(), name="transaction-detail"),
]
