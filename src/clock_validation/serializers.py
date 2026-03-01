from rest_framework import serializers

from clock_event.serializers import ClockEventSerializer

from .models import ClockValidationCode


class ClockValidationCodeSerializer(serializers.ModelSerializer):
    """
    Réponse renvoyée à l'employé après un clock-in ou clock-out.
    Expose le code, son expiration et le ClockEvent lié.
    """

    clock_event = ClockEventSerializer(read_only=True)
    seconds_remaining = serializers.SerializerMethodField()
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ClockValidationCode
        fields = [
            "id",
            "clock_event",
            "code",
            "status",
            "status_label",
            "expires_at",
            "seconds_remaining",
            "created_at",
        ]
        read_only_fields = fields

    def get_seconds_remaining(self, obj) -> int:
        return obj.seconds_remaining


# ─────────────────────────────────────────────────────────────────────────────
# SUBMIT
# ─────────────────────────────────────────────────────────────────────────────


class SubmitCodeSerializer(serializers.Serializer):
    """Payload pour soumettre un code de validation."""

    code = serializers.CharField(
        min_length=6,
        max_length=6,
        help_text="Code numérique à 6 chiffres reçu après le pointage.",
    )

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(
                "Le code doit être composé uniquement de chiffres."
            )
        return value
