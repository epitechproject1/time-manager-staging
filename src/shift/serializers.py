from rest_framework import serializers

from assignment.serializers import ScheduleAssignmentSerializer
from shift.models import Shift
from users.serializers import UserSerializer


class ShiftSerializer(serializers.ModelSerializer):
    """
    Serializer des occurrences réelles de planning.
    """

    user_detail = UserSerializer(source="user", read_only=True)
    assignment_detail = ScheduleAssignmentSerializer(
        source="assignment", read_only=True
    )

    # 👉 display du type de shift
    shift_type_display = serializers.CharField(
        source="get_shift_type_display",
        read_only=True,
    )

    class Meta:
        model = Shift
        fields = [
            "id",
            "user",
            "user_detail",
            "assignment",
            "assignment_detail",
            "date",
            "start_time",
            "end_time",
            "shift_type",
            "shift_type_display",  # ✅ display ajouté
            "overridden",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate(self, attrs):
        """
        Validation cohérente avec la logique métier du modèle.
        """

        shift_type = attrs.get(
            "shift_type",
            getattr(self.instance, "shift_type", None),
        )
        start_time = attrs.get(
            "start_time",
            getattr(self.instance, "start_time", None),
        )
        end_time = attrs.get(
            "end_time",
            getattr(self.instance, "end_time", None),
        )

        if shift_type in [Shift.ShiftType.WORK, Shift.ShiftType.BREAK]:
            if not start_time or not end_time:
                raise serializers.ValidationError(
                    "Les heures sont obligatoires pour un shift WORK ou BREAK."
                )

            if end_time <= start_time:
                raise serializers.ValidationError("Heure de fin invalide.")

        if shift_type in [Shift.ShiftType.HOLIDAY, Shift.ShiftType.OFF]:
            if start_time or end_time:
                raise serializers.ValidationError(
                    "Un shift HOLIDAY ou OFF ne doit pas avoir d'heures."
                )

        return attrs
