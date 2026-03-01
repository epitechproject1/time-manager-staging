from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from shift.models import Shift

User = settings.AUTH_USER_MODEL


class ClockEvent(models.Model):
    """
    Événement de pointage individuel.
    Chaque début et fin de shift génère un ClockEvent distinct.
    Le statut est géré exclusivement par ClockValidationCode.
    """

    class EventType(models.TextChoices):
        CLOCK_IN = "CLOCK_IN", "Début de shift"
        CLOCK_OUT = "CLOCK_OUT", "Fin de shift"

    class Status(models.TextChoices):
        PENDING = "PENDING", "En attente"
        APPROVED = "APPROVED", "Approuvé"
        REJECTED = "REJECTED", "Rejeté"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="clock_events",
    )

    shift = models.ForeignKey(
        Shift,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clock_events",
    )

    event_type = models.CharField(
        max_length=10,
        choices=EventType.choices,
    )

    timestamp = models.DateTimeField()

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )

    # Note interne — remplie par ClockValidationCode en cas de rejet
    note = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["shift", "event_type"]),
            models.Index(fields=["status"]),
        ]

    # ─────────────────────────────
    # VALIDATION MÉTIER
    # ─────────────────────────────
    def clean(self):
        if self.shift:
            # Le shift doit appartenir au même utilisateur
            if self.shift.user != self.user:
                raise ValidationError("Le shift ne correspond pas à cet utilisateur.")

            # Un seul événement de chaque type par shift
            existing = ClockEvent.objects.filter(
                shift=self.shift,
                event_type=self.event_type,
            ).exclude(pk=self.pk)

            if existing.exists():
                raise ValidationError(
                    f"Un événement {self.event_type} existe déjà pour ce shift."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    # ─────────────────────────────
    # HELPERS
    # ─────────────────────────────
    @property
    def is_pending(self) -> bool:
        return self.status == self.Status.PENDING

    @property
    def is_approved(self) -> bool:
        return self.status == self.Status.APPROVED

    @property
    def is_rejected(self) -> bool:
        return self.status == self.Status.REJECTED

    def __str__(self):
        return (
            f"{self.user} — {self.get_event_type_display()} "
            f"— {self.timestamp:%d/%m/%Y %H:%M} — {self.get_status_display()}"
        )
