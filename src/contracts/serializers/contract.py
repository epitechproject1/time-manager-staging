from rest_framework import serializers

from contracts.models import Contract
from contracts.serializers.contract_type import ContractTypeSerializer


class ContractSerializer(serializers.ModelSerializer):
    """
    Serializer principal du contrat.
    """

    # Pour afficher les infos du type de contrat en lecture
    contract_type_detail = ContractTypeSerializer(
        source="contract_type", read_only=True
    )

    class Meta:
        model = Contract
        fields = [
            "id",
            "user",
            "contract_type",
            "contract_type_detail",
            "start_date",
            "end_date",
            "weekly_hours_target",
            "created_at",
        ]
        read_only_fields = ["created_at"]

    def validate(self, data):
        """
        Validation métier côté API.
        """

        contract_type = data.get("contract_type")
        end_date = data.get("end_date")
        start_date = data.get("start_date")

        # Vérifie si le type exige une date de fin
        if contract_type and contract_type.requires_end_date and not end_date:
            raise serializers.ValidationError(
                "Ce type de contrat nécessite une date de fin."
            )

        # Vérifie la cohérence des dates
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                "La date de fin doit être après la date de début."
            )

        return data
