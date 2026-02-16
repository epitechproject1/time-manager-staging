from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .assignment import ScheduleAssignment

User = settings.AUTH_USER_MODEL


class Shift(models.Model):
    """
    Représente un créneau réel dans le calendrier.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shifts")

    assignment = models.ForeignKey(
        ScheduleAssignment, on_delete=models.PROTECT, related_name="shifts"
    )

    date = models.DateField()

    start_time = models.TimeField()
    end_time = models.TimeField()

    overridden = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "start_time"]
        unique_together = ("user", "date", "start_time", "end_time")
        indexes = [
            models.Index(fields=["user", "date"]),
        ]

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("Heure de fin invalide.")

    def __str__(self):
        return f"{self.user} {self.date} {self.start_time}-{self.end_time}"
