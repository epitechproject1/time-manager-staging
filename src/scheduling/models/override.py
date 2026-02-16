from django.db import models

from .shift import Shift


class ShiftOverride(models.Model):
    """
    Exception appliquée à un shift.
    Permet de modifier ou annuler un créneau.
    """

    shift = models.OneToOneField(
        Shift, on_delete=models.CASCADE, related_name="override"
    )

    new_start_time = models.TimeField(null=True, blank=True)
    new_end_time = models.TimeField(null=True, blank=True)

    cancelled = models.BooleanField(default=False)

    reason = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Override {self.shift}"
