from rest_framework import serializers

from scheduling.models import ShiftOverride
from scheduling.serializers.shift import ShiftSerializer


class ShiftOverrideSerializer(serializers.ModelSerializer):
    """
    Serializer des exceptions de planning.
    """

    shift_detail = ShiftSerializer(source="shift", read_only=True)

    class Meta:
        model = ShiftOverride
        fields = [
            "id",
            "shift",
            "shift_detail",
            "new_start_time",
            "new_end_time",
            "cancelled",
            "reason",
            "created_at",
        ]
        read_only_fields = ["created_at"]
