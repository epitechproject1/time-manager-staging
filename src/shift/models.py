from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from assignment.models import ScheduleAssignment

User = settings.AUTH_USER_MODEL


class Shift(models.Model):
    """
    Représente un créneau réel dans le calendrier.
    """

    class ShiftType(models.TextChoices):
        WORK = "WORK", "Travail"
        BREAK = "BREAK", "Pause"
        HOLIDAY = "HOLIDAY", "Jour férié"
        OFF = "OFF", "Repos"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shifts",
    )

    assignment = models.ForeignKey(
        ScheduleAssignment,
        on_delete=models.PROTECT,
        related_name="shifts",
    )

    date = models.DateField()

    # 👉 heures optionnelles pour permettre HOLIDAY / OFF
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)

    shift_type = models.CharField(
        max_length=10,
        choices=ShiftType.choices,
        default=ShiftType.WORK,
    )

    overridden = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "start_time"]
        unique_together = ("user", "date", "start_time", "end_time")
        indexes = [
            models.Index(fields=["user", "date"]),
            models.Index(fields=["shift_type"]),
        ]

    def clean(self):
        """
        Validation métier.
        """

        # 👉 si c'est un shift WORK ou BREAK → heures obligatoires
        if self.shift_type in [self.ShiftType.WORK, self.ShiftType.BREAK]:
            if not self.start_time or not self.end_time:
                raise ValidationError(
                    "Les heures sont obligatoires pour un shift WORK ou BREAK."
                )

            if self.end_time <= self.start_time:
                raise ValidationError("Heure de fin invalide.")

        # 👉 si HOLIDAY ou OFF → pas d'heures
        if self.shift_type in [self.ShiftType.HOLIDAY, self.ShiftType.OFF]:
            if self.start_time or self.end_time:
                raise ValidationError(
                    "Un shift HOLIDAY ou OFF ne doit pas avoir d'heures."
                )

    def __str__(self):
        if self.start_time and self.end_time:
            return f"{self.user} {self.date} {self.start_time}-{self.end_time}"
        return f"{self.user} {self.date} ({self.shift_type})"
