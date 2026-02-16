from rest_framework import serializers

from contracts.serializers.contract import ContractSerializer
from planning_patterns.serializers.week_pattern import WeekPatternSerializer
from scheduling.models import ScheduleAssignment


class ScheduleAssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer pour relier un contrat à un planning.
    """

    contract_detail = ContractSerializer(source="contract", read_only=True)
    week_pattern_detail = WeekPatternSerializer(source="week_pattern", read_only=True)

    class Meta:
        model = ScheduleAssignment
        fields = [
            "id",
            "contract",
            "contract_detail",
            "week_pattern",
            "week_pattern_detail",
            "start_date",
            "end_date",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate(self, data):
        if data.get("end_date") and data["end_date"] < data["start_date"]:
            raise serializers.ValidationError(
                "La date de fin doit être après la date de début."
            )
        return data
