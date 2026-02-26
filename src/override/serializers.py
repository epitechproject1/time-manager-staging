# scheduling/serializers/shift_override.py

from rest_framework import serializers

from override.models import ShiftOverride
from shift.serializers import ShiftSerializer


class ShiftOverrideSerializer(serializers.ModelSerializer):
    shift_detail = ShiftSerializer(source="shift", read_only=True)

    reason_label = serializers.CharField(
        source="get_reason_code_display", read_only=True
    )

    class Meta:
        model = ShiftOverride
        fields = [
            "id",
            "shift",
            "shift_detail",
            "new_start_time",
            "new_end_time",
            "cancelled",
            "reason_code",
            "reason_label",
            "reason_note",
            "created_at",
        ]
        read_only_fields = ["created_at"]
