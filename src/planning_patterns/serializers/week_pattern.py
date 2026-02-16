from rest_framework import serializers

from planning_patterns.models import WeekPattern
from planning_patterns.serializers.time_slot_pattern import TimeSlotPatternSerializer


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
