from rest_framework import serializers

from time_slot_pattern.models import TimeSlotPattern


class TimeSlotPatternSerializer(serializers.ModelSerializer):
    """
    Serializer des créneaux horaires d’une semaine type.
    """

    # Labels calculés
    weekday_label = serializers.SerializerMethodField()
    slot_type_label = serializers.CharField(
        source="get_slot_type_display",
        read_only=True,
    )

    class Meta:
        model = TimeSlotPattern
        fields = [
            "id",
            "week_pattern",
            "weekday",
            "weekday_label",
            "start_time",
            "end_time",
            "slot_type",
            "slot_type_label",
        ]

    # ==============================
    # LABELS
    # ==============================
    def get_weekday_label(self, obj):
        labels = [
            "Lundi",
            "Mardi",
            "Mercredi",
            "Jeudi",
            "Vendredi",
            "Samedi",
            "Dimanche",
        ]
        return labels[obj.weekday]

    # ==============================
    # VALIDATION
    # ==============================
    def validate(self, data):
        start = data.get("start_time")
        end = data.get("end_time")

        # Cas update partiel
        if self.instance:
            start = start or self.instance.start_time
            end = end or self.instance.end_time

        if end <= start:
            raise serializers.ValidationError(
                "L'heure de fin doit être après l'heure de début."
            )

        return data
