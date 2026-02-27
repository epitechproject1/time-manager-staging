from rest_framework import serializers

from contracts.models.contract_type import ContractType


class ContractTypeSerializer(serializers.ModelSerializer):
    """
    Serializer pour gérer les types de contrat.
    Permet création, lecture et modification via l'API.
    """

    class Meta:
        model = ContractType
        fields = [
            "id",
            "name",
            "code",
            "description",
            "requires_end_date",
        ]
