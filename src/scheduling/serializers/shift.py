from rest_framework import serializers

from scheduling.models import Shift


class ShiftSerializer(serializers.ModelSerializer):
    """
    Serializer des occurrences réelles de planning.
    """

    class Meta:
        model = Shift
        fields = [
            "id",
            "user",
            "assignment",
            "date",
            "start_time",
            "end_time",
            "overridden",
            "created_at",
        ]
        read_only_fields = ["created_at"]
