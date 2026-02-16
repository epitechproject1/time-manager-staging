from rest_framework import serializers

from planning_patterns.models import PlanningTemplate
from planning_patterns.serializers.week_pattern import WeekPatternSerializer


class PlanningTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer du template de planning.
    """

    # Affichage du pattern en lecture
    week_pattern_detail = WeekPatternSerializer(source="week_pattern", read_only=True)

    class Meta:
        model = PlanningTemplate
        fields = [
            "id",
            "name",
            "week_pattern",
            "week_pattern_detail",
            "weekly_hours_target",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["created_at"]
