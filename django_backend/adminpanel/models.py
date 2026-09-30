from django.conf import settings
from django.db import models


class AdminLog(models.Model):
    class Action(models.TextChoices):
        EXPORT_CSV = "EXPORT_CSV", "Export CSV"
        USER_ACTIVATED = "USER_ACTIVATED", "User activated"
        USER_DEACTIVATED = "USER_DEACTIVATED", "User deactivated"
        VIEW_SUMMARY = "VIEW_SUMMARY", "View daily summary"

    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
                              related_name="admin_logs")
    action = models.CharField(max_length=20, choices=Action.choices)
    details = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "admin_logs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.admin} {self.action}"
