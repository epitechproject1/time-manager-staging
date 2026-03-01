from rest_framework import serializers

from assignment.serializers import ScheduleAssignmentSerializer
from clock_event.models import ClockEvent
from shift.models import Shift
from users.serializers import UserSerializer


class ShiftSerializer(serializers.ModelSerializer):
    """
    Serializer des occurrences réelles de planning.
    Inclut le statut de pointage calculé.
    """

    user_detail = UserSerializer(source="user", read_only=True)
    assignment_detail = ScheduleAssignmentSerializer(
        source="assignment", read_only=True
    )

    shift_type_display = serializers.CharField(
        source="get_shift_type_display",
        read_only=True,
    )

    clock_status = serializers.SerializerMethodField()

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
            "shift_type_display",
            "clock_status",  # ✅ ajouté
            "overridden",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    # ─────────────────────────────
    # CLOCK STATUS
    # ─────────────────────────────
    def get_clock_status(self, obj):
        """
        Retourne le statut de pointage basé sur les ClockEvents.
        """

        events = obj.clock_events.all()

        clock_in = next(
            (e for e in events if e.event_type == ClockEvent.EventType.CLOCK_IN),
            None,
        )

        clock_out = next(
            (e for e in events if e.event_type == ClockEvent.EventType.CLOCK_OUT),
            None,
        )

        if not clock_in:
            return "NOT_STARTED"

        if clock_in.status == ClockEvent.Status.PENDING:
            return "CLOCK_IN_PENDING"

        if clock_in.status == ClockEvent.Status.APPROVED and not clock_out:
            return "IN_PROGRESS"

        if clock_out and clock_out.status == ClockEvent.Status.PENDING:
            return "CLOCK_OUT_PENDING"

        if clock_out and clock_out.status == ClockEvent.Status.APPROVED:
            return "COMPLETED"

        return "NOT_STARTED"

    # ─────────────────────────────
    # VALIDATION MÉTIER
    # ─────────────────────────────
    def validate(self, attrs):
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
