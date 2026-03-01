from rest_framework import serializers

from time_slot_pattern.serializers import TimeSlotPatternSerializer
from week_pattern.models import WeekPattern


class WeekPatternSerializer(serializers.ModelSerializer):
    """
    Serializer de la semaine type.
    """

    # Affichage des créneaux en lecture
    time_slots = TimeSlotPatternSerializer(many=True, read_only=True)

    class Meta:
        model = WeekPattern
        fields = [
            "id",
            "name",
            "description",
            "created_at",
            "time_slots",
        ]
