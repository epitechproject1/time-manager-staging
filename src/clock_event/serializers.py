from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import serializers

from shift.models import Shift

from .models import ClockEvent

# ─────────────────────────────────────
# CONFIG
# ─────────────────────────────────────
CLOCK_IN_TOLERANCE_MINUTES = settings.CLOCK_IN_TOLERANCE_MINUTES
CLOCK_OUT_TOLERANCE_MINUTES = settings.CLOCK_OUT_TOLERANCE_MINUTES


# ─────────────────────────────────────
# CLOCK EVENT (LECTURE)
# ─────────────────────────────────────
class ClockEventSerializer(serializers.ModelSerializer):
    """
    Serializer de lecture d'un ClockEvent.
    """

    user_email = serializers.EmailField(source="user.email", read_only=True)
    shift_date = serializers.DateField(source="shift.date", read_only=True)

    event_type_label = serializers.CharField(
        source="get_event_type_display",
        read_only=True,
    )

    status_label = serializers.CharField(
        source="get_status_display",
        read_only=True,
    )

    class Meta:
        model = ClockEvent
        fields = [
            "id",
            "user",
            "user_email",
            "shift",
            "shift_date",
            "event_type",
            "event_type_label",
            "timestamp",
            "status",
            "status_label",
            "note",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "user_email",
            "shift_date",
            "event_type_label",
            "status",
            "status_label",
            "note",
            "created_at",
        ]


# ─────────────────────────────────────
# HELPERS
# ─────────────────────────────────────
def get_shift_datetimes(shift: Shift):
    """Retourne les datetime aware du début et de la fin du shift."""
    start_dt = timezone.make_aware(datetime.combine(shift.date, shift.start_time))
    end_dt = timezone.make_aware(datetime.combine(shift.date, shift.end_time))
    return start_dt, end_dt


# ─────────────────────────────────────
# CLOCK IN
# ─────────────────────────────────────
class ClockInSerializer(serializers.Serializer):
    """
    Payload pour pointer le début d'un shift.
    """

    shift = serializers.PrimaryKeyRelatedField(queryset=Shift.objects.all())

    def validate(self, data):
        request = self.context["request"]
        shift = data["shift"]
        now = timezone.localtime()

        # ───── utilisateur propriétaire
        if shift.user != request.user:
            raise serializers.ValidationError("Vous ne pouvez pas pointer ce shift.")

        # ───── type autorisé
        if shift.shift_type not in [Shift.ShiftType.WORK, Shift.ShiftType.BREAK]:
            raise serializers.ValidationError("Impossible de pointer ce type de shift.")

        # ───── déjà pointé
        if ClockEvent.objects.filter(
            shift=shift,
            event_type=ClockEvent.EventType.CLOCK_IN,
        ).exists():
            raise serializers.ValidationError("Un pointage d'entrée existe déjà.")

        start_dt, end_dt = get_shift_datetimes(shift)
        tolerance = timedelta(minutes=CLOCK_IN_TOLERANCE_MINUTES)

        # ───── uniquement aujourd’hui
        if shift.date != now.date():
            raise serializers.ValidationError(
                "Vous ne pouvez pointer que les shifts du jour."
            )

        # ───── trop tôt
        if now < start_dt - tolerance:
            raise serializers.ValidationError("Le shift n’a pas encore commencé.")

        # ───── trop tard
        if now > end_dt:
            raise serializers.ValidationError("Le shift est terminé.")

        return data


# ─────────────────────────────────────
# CLOCK OUT
# ─────────────────────────────────────
class ClockOutSerializer(serializers.Serializer):
    """
    Payload pour pointer la fin d'un shift.
    """

    shift = serializers.PrimaryKeyRelatedField(queryset=Shift.objects.all())

    def validate(self, data):
        request = self.context["request"]
        shift = data["shift"]
        now = timezone.localtime()

        # ───── utilisateur propriétaire
        if shift.user != request.user:
            raise serializers.ValidationError("Vous ne pouvez pas pointer ce shift.")

        # ───── CLOCK IN obligatoire
        if not ClockEvent.objects.filter(
            shift=shift,
            event_type=ClockEvent.EventType.CLOCK_IN,
            status=ClockEvent.Status.APPROVED,
        ).exists():
            raise serializers.ValidationError("Aucun pointage d'entrée approuvé.")

        # ───── déjà clock out
        if ClockEvent.objects.filter(
            shift=shift,
            event_type=ClockEvent.EventType.CLOCK_OUT,
        ).exists():
            raise serializers.ValidationError("Un pointage de sortie existe déjà.")

        start_dt, end_dt = get_shift_datetimes(shift)
        tolerance = timedelta(minutes=CLOCK_OUT_TOLERANCE_MINUTES)

        # ───── uniquement aujourd’hui
        if shift.date != now.date():
            raise serializers.ValidationError(
                "Impossible de pointer ce shift aujourd’hui."
            )

        # ───── pas encore commencé
        if now < start_dt:
            raise serializers.ValidationError("Le shift n’a pas encore commencé.")

        # ───── trop tard
        if now > end_dt + tolerance:
            raise serializers.ValidationError("La fenêtre de pointage est expirée.")

        return data
