from rest_framework import serializers

from shift.models import Shift

from .models import ClockEvent


class ClockEventSerializer(serializers.ModelSerializer):
    """
    Lecture d'un ClockEvent.
    Utilisé dans les réponses, le listing et par clock_validation.
    """

    user_email = serializers.EmailField(source="user.email", read_only=True)
    shift_date = serializers.DateField(source="shift.date", read_only=True)
    event_type_label = serializers.CharField(
        source="get_event_type_display", read_only=True
    )
    status_label = serializers.CharField(source="get_status_display", read_only=True)

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


# ─────────────────────────────────────────────────────────────────────────────
# CLOCK IN
# ─────────────────────────────────────────────────────────────────────────────


class ClockInSerializer(serializers.Serializer):
    """Payload pour pointer le début d'un shift."""

    shift_id = serializers.IntegerField()

    def validate_shift_id(self, value):
        try:
            shift = Shift.objects.get(pk=value)
        except Shift.DoesNotExist:
            raise serializers.ValidationError("Shift introuvable.")

        if shift.shift_type not in [Shift.ShiftType.WORK, Shift.ShiftType.BREAK]:
            raise serializers.ValidationError(
                "Impossible de pointer sur un shift de type HOLIDAY ou OFF."
            )

        if ClockEvent.objects.filter(
            shift=shift,
            event_type=ClockEvent.EventType.CLOCK_IN,
        ).exists():
            raise serializers.ValidationError(
                "Un pointage d'entrée existe déjà pour ce shift."
            )

        return value


# ─────────────────────────────────────────────────────────────────────────────
# CLOCK OUT
# ─────────────────────────────────────────────────────────────────────────────


class ClockOutSerializer(serializers.Serializer):
    """Payload pour pointer la fin d'un shift."""

    shift_id = serializers.IntegerField()

    def validate_shift_id(self, value):
        try:
            shift = Shift.objects.get(pk=value)
        except Shift.DoesNotExist:
            raise serializers.ValidationError("Shift introuvable.")

        # Un CLOCK_IN approuvé doit exister avant de pouvoir faire un CLOCK_OUT
        if not ClockEvent.objects.filter(
            shift=shift,
            event_type=ClockEvent.EventType.CLOCK_IN,
            status=ClockEvent.Status.APPROVED,
        ).exists():
            raise serializers.ValidationError(
                "Aucun pointage d'entrée approuvé pour ce shift."
            )

        if ClockEvent.objects.filter(
            shift=shift,
            event_type=ClockEvent.EventType.CLOCK_OUT,
        ).exists():
            raise serializers.ValidationError(
                "Un pointage de sortie existe déjà pour ce shift."
            )

        return value
