from django.core.exceptions import ValidationError
from django.db import models

from .week_pattern import WeekPattern


class TimeSlotPattern(models.Model):
    """
    Créneau horaire dans une semaine type.
    """

    WORK = "WORK"
    BREAK = "BREAK"

    SLOT_TYPES = [
        (WORK, "Work"),
        (BREAK, "Break"),
    ]

    # 🔗 Relation vers la semaine type
    week_pattern = models.ForeignKey(
        WeekPattern, on_delete=models.CASCADE, related_name="time_slots"
    )

    # Jour de la semaine (0 = lundi, 6 = dimanche)
    weekday = models.PositiveSmallIntegerField()

    # Heure de début
    start_time = models.TimeField()

    # Heure de fin
    end_time = models.TimeField()

    # Type de créneau (travail ou pause)
    slot_type = models.CharField(max_length=10, choices=SLOT_TYPES, default=WORK)

    class Meta:
        ordering = ["weekday", "start_time"]
        indexes = [
            models.Index(fields=["week_pattern", "weekday"]),
        ]

    def clean(self):
        """
        Validation métier.
        """
        if self.end_time <= self.start_time:
            raise ValidationError("L'heure de fin doit être après l'heure de début.")

        if not 0 <= self.weekday <= 6:
            raise ValidationError("weekday doit être compris entre 0 et 6.")

    def __str__(self):
        return f"{self.week_pattern} - {self.weekday} {self.start_time}-{self.end_time}"
