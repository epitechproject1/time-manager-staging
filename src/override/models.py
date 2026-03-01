# scheduling/models/shift_override.py

from django.core.exceptions import ValidationError
from django.db import models

from shift.models import Shift


class ShiftOverride(models.Model):
    """
    Exception appliquée à un shift.

    Permet :
    - d'annuler un shift
    - de modifier ses horaires
    """

    # ─────────────────────────────
    # ENUM RAISONS
    # ─────────────────────────────
    class Reason(models.TextChoices):
        SICK = "SICK", "Maladie"
        LEAVE = "LEAVE", "Congé"
        TRAINING = "TRAINING", "Formation"
        MEETING = "MEETING", "Réunion"
        CANCELLED = "CANCELLED", "Annulation"
        OTHER = "OTHER", "Autre"

    # ─────────────────────────────
    # RELATION
    # ─────────────────────────────
    shift = models.OneToOneField(
        Shift,
        on_delete=models.CASCADE,
        related_name="override",
    )

    # ─────────────────────────────
    # NOUVEAUX HORAIRES
    # ─────────────────────────────
    new_start_time = models.TimeField(null=True, blank=True)
    new_end_time = models.TimeField(null=True, blank=True)

    # ─────────────────────────────
    # ANNULATION
    # ─────────────────────────────
    cancelled = models.BooleanField(default=False)

    # ─────────────────────────────
    # RAISON
    # ─────────────────────────────
    reason_code = models.CharField(
        max_length=20,
        choices=Reason.choices,
        null=True,
        blank=True,
    )

    reason_note = models.CharField(
        max_length=255,
        blank=True,
    )

    # ─────────────────────────────
    # META
    # ─────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)

    # ─────────────────────────────
    # VALIDATION MÉTIER
    # ─────────────────────────────
    def clean(self):
        # ❌ un override doit soit modifier les horaires soit annuler
        if not self.cancelled and not (self.new_start_time or self.new_end_time):
            raise ValidationError(
                "Un override doit modifier les horaires ou annuler le shift."
            )

        # ❌ si annulé → pas d’horaires
        if self.cancelled and (self.new_start_time or self.new_end_time):
            raise ValidationError("Un shift annulé ne doit pas avoir d'horaires.")

        # ❌ cohérence heures
        if self.new_start_time and self.new_end_time:
            if self.new_end_time <= self.new_start_time:
                raise ValidationError("Heure de fin invalide.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    # ─────────────────────────────
    # HELPERS
    # ─────────────────────────────
    @property
    def is_time_override(self):
        return not self.cancelled and (self.new_start_time or self.new_end_time)

    @property
    def reason_label(self):
        return self.get_reason_code_display()

    # ─────────────────────────────
    # STRING
    # ─────────────────────────────
    def __str__(self):
        if self.cancelled:
            return f"Override {self.shift} — annulé"
        if self.is_time_override:
            return f"Override {self.shift} — horaires modifiés"
        return f"Override {self.shift}"
