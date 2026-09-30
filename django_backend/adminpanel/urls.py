from django.urls import path

from . import views

urlpatterns = [
    path("users/", views.AdminUserListView.as_view(), name="admin-users"),
    path("users/<int:pk>/", views.AdminUserDetailView.as_view(), name="admin-user-detail"),
    path("cards/", views.AdminCardListView.as_view(), name="admin-cards"),
    path("transactions/", views.AdminTransactionListView.as_view(), name="admin-transactions"),
    path("logs/", views.AdminLogListView.as_view(), name="admin-logs"),
    path("daily-summary/", views.DailySummaryView.as_view(), name="admin-daily-summary"),
]
