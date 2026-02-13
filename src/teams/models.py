from django.conf import settings
from django.db import models


class Teams(models.Model):
    name = models.CharField(max_length=150, db_index=True)
    description = models.TextField(db_index=True)

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_teams",
        verbose_name="Propriétaire",
    )

    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teams",
        verbose_name="Département",
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="teams",
        blank=True,
        verbose_name="Membres",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}: {self.description[:50]}"

    class Meta:
        db_table = "teams"
        verbose_name = "Team"
        verbose_name_plural = "Teams"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["name", "created_at"]),
            models.Index(fields=["-created_at"]),
        ]
