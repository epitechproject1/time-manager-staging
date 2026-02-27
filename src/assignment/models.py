from django.core.exceptions import ValidationError
from django.db import models

from contracts.models import Contract
from week_pattern.models import WeekPattern


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

    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["contract"]),
            models.Index(fields=["week_pattern"]),
        ]

    def clean(self):
        # Cohérence interne
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("La date de fin doit être après la date de début.")

        # 🚨 Nouvelle validation métier
        contract = self.contract

        # Début assignment avant début contrat
        if self.start_date < contract.start_date:
            raise ValidationError(
                "La période du planning ne peut pas commencer avant le contrat."
            )

        # Fin assignment après fin contrat
        if contract.end_date:
            if not self.end_date:
                raise ValidationError(
                    "Ce contrat a une date de fin. Le planning doit en avoir une."
                )

            if self.end_date > contract.end_date:
                raise ValidationError(
                    "La période du planning ne peut pas dépasser la fin du contrat."
                )

    def __str__(self):
        return f"{self.contract} → {self.week_pattern}"
