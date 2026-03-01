import secrets
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from clock_event.models import ClockEvent
from notifications.services import send_clock_validation_code

EXPIRY_MINUTES = settings.EXPIRY_MINUTES


class ClockValidationCode(models.Model):
    """
    Code numérique à 6 chiffres, à usage unique, valable 3 minutes.

    Cycle de vie :
      PENDING  → code généré, en attente de soumission
      USED     → code soumis et correct → ClockEvent APPROVED
      EXPIRED  → code expiré ou incorrect → ClockEvent REJECTED
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "En attente"
        USED = "USED", "Utilisé"
        EXPIRED = "EXPIRED", "Expiré"

    clock_event = models.OneToOneField(
        ClockEvent,
        on_delete=models.CASCADE,
        related_name="validation_code",
    )

    code = models.CharField(max_length=6)

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["code", "status"]),
            models.Index(fields=["expires_at", "status"]),
        ]

    # ─────────────────────────────
    # FACTORY
    # ─────────────────────────────
    @classmethod
    def create_for_event(cls, clock_event: ClockEvent) -> "ClockValidationCode":
        """
        Crée le code, le persiste et envoie l'email de validation.
        Point d'entrée unique — toujours utiliser cette méthode.
        """
        expires_at = timezone.now() + timedelta(minutes=EXPIRY_MINUTES)
        code = cls._generate_code()

        instance = cls.objects.create(
            clock_event=clock_event,
            code=code,
            expires_at=expires_at,
        )

        send_clock_validation_code(
            user=clock_event.user,
            code=code,
            event_type=clock_event.event_type,
            expires_at=expires_at,
        )

        return instance

    @staticmethod
    def _generate_code() -> str:
        """Code numérique à 6 chiffres, cryptographiquement sûr."""
        return str(secrets.randbelow(1_000_000)).zfill(6)

    # ─────────────────────────────
    # ÉTAT
    # ─────────────────────────────
    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return self.status == self.Status.PENDING and not self.is_expired

    @property
    def seconds_remaining(self) -> int:
        delta = self.expires_at - timezone.now()
        return max(0, int(delta.total_seconds()))

    # ─────────────────────────────
    # VALIDATION
    # ─────────────────────────────
    def verify(self, submitted_code: str) -> bool:
        """
        Vérifie le code soumis par l'employé.

        Cas possibles :
          - Déjà traité             → False (sans effet)
          - Expiré                  → ClockEvent REJECTED, False
          - Mauvais code            → ClockEvent REJECTED, False
          - Correct dans le délai   → ClockEvent APPROVED, True
        """
        if self.status != self.Status.PENDING:
            return False

        if self.is_expired:
            self._reject("Expiré")
            return False

        if self.code != submitted_code:
            self._reject("Code incorrect")
            return False

        # ✅ Succès
        self.status = self.Status.USED
        self.save(update_fields=["status"])

        self.clock_event.status = ClockEvent.Status.APPROVED
        self.clock_event.save(update_fields=["status"])

        return True

    def _reject(self, reason: str = "") -> None:
        """Passe le code en EXPIRED et le ClockEvent associé en REJECTED."""
        self.status = self.Status.EXPIRED
        self.save(update_fields=["status"])

        self.clock_event.status = ClockEvent.Status.REJECTED
        self.clock_event.note = reason
        self.clock_event.save(update_fields=["status", "note"])

    def __str__(self):
        return (
            f"Code {self.code} — {self.clock_event} "
            f"— {self.get_status_display()} "
            f"— expire {self.expires_at:%H:%M:%S}"
        )
