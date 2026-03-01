from datetime import timedelta

from django.db import models
from django.utils import timezone

from users.models import User


class PasswordResetCode(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reset_codes",
    )

    code = models.CharField(max_length=6)

    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "code"]),
            models.Index(fields=["expires_at"]),
        ]

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()

    @staticmethod
    def generate_expiration(minutes=10):
        return timezone.now() + timedelta(minutes=minutes)

    def __str__(self):
        return f"{self.user.email} - {self.code}"
