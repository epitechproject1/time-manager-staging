from django.conf import settings
from django.db import models

from .constants import PermissionType


class Permission(models.Model):
    """
    Permission accordée à un utilisateur par un autre utilisateur.
    """

    permission_type = models.CharField(
        max_length=20,
        choices=PermissionType.choices,
    )

    start_date = models.DateField()
    end_date = models.DateField(
        null=True,
        blank=True,
    )

    granted_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="granted_permissions",
    )

    granted_to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_permissions",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "permissions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["permission_type"]),
            models.Index(fields=["granted_to_user"]),
        ]
        models.CheckConstraint(
            condition=models.Q(end_date__gte=models.F("start_date"))
            | models.Q(end_date__isnull=True),
            name="permission_end_date_after_start_date",
        )

    def __str__(self) -> str:
        return (
            f"{self.permission_type} "
            f"→ {self.granted_to_user} "
            f"(by {self.granted_by_user})"
        )
