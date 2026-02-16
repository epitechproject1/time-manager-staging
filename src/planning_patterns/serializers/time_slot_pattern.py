from rest_framework import serializers

from planning_patterns.models import TimeSlotPattern


class TimeSlotPatternSerializer(serializers.ModelSerializer):
    """
    Serializer des créneaux horaires d’une semaine type.
    """

    class Meta:
        model = TimeSlotPattern
        fields = [
            "id",
            "week_pattern",
            "weekday",
            "start_time",
            "end_time",
            "slot_type",
        ]

    def validate(self, data):
        """
        Validation métier.
        """
        if data["end_time"] <= data["start_time"]:
            raise serializers.ValidationError(
                "L'heure de fin doit être après l'heure de début."
            )
        return data
