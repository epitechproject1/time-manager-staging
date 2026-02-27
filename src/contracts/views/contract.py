from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from contracts.models import Contract
from contracts.serializers.contract import ContractSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Contracts"],
        summary="Lister les contrats",
        description="Liste de tous les contrats.",
    ),
    retrieve=extend_schema(
        tags=["Contracts"],
        summary="Détail d’un contrat",
    ),
    create=extend_schema(
        tags=["Contracts"],
        summary="Créer un contrat",
    ),
    update=extend_schema(
        tags=["Contracts"],
        summary="Mettre à jour un contrat",
    ),
    partial_update=extend_schema(
        tags=["Contracts"],
        summary="Mettre à jour partiellement un contrat",
    ),
    destroy=extend_schema(
        tags=["Contracts"],
        summary="Supprimer un contrat",
    ),
)
class ContractViewSet(ModelViewSet):
    """
    CRUD des contrats.
    """

    queryset = Contract.objects.select_related("contract_type", "user").all()
    serializer_class = ContractSerializer
