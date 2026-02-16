from django.core.exceptions import ValidationError
from django.db import models

from contracts.models import Contract
from planning_patterns.models import WeekPattern


class ScheduleAssignment(models.Model):
    """
    Relie un contrat à une semaine type sur une période donnée.
    """

    contract = models.ForeignKey(
        Contract, on_delete=models.CASCADE, related_name="assignments"
    )

    week_pattern = models.ForeignKey(
        WeekPattern, on_delete=models.PROTECT, related_name="assignments"
    )

    # période d'application du planning
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    # statut (optionnel mais utile)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["contract"]),
            models.Index(fields=["week_pattern"]),
        ]

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("La date de fin doit être après la date de début.")

    def __str__(self):
        return f"{self.contract} → {self.week_pattern}"
