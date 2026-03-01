from rest_framework import serializers

from assignment.models import ScheduleAssignment
from contracts.serializers import ContractSerializer
from week_pattern.serializers import WeekPatternSerializer


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

    def validate(self, attrs):
        """
        Validation cohérente avec les règles métier du modèle.
        Compatible create et update.
        """

        contract = attrs.get(
            "contract",
            getattr(self.instance, "contract", None),
        )
        start_date = attrs.get(
            "start_date",
            getattr(self.instance, "start_date", None),
        )
        end_date = attrs.get(
            "end_date",
            getattr(self.instance, "end_date", None),
        )

        # Cohérence interne
        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError(
                "La date de fin doit être après la date de début."
            )

        if contract and start_date:
            # Début assignment avant contrat
            if start_date < contract.start_date:
                raise serializers.ValidationError(
                    "La période du planning ne peut pas commencer avant le contrat."
                )

            # Si contrat avec fin → assignment doit respecter
            if contract.end_date:
                if not end_date:
                    raise serializers.ValidationError(
                        "Ce contrat a une date de fin. Le planning doit en avoir une."
                    )

                if end_date > contract.end_date:
                    raise serializers.ValidationError(
                        "La période du planning ne peut pas dépasser la fin du contrat."
                    )

        return attrs
