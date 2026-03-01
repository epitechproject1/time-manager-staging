from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from contracts.models import ContractType
from contracts.serializers.contract_type import ContractTypeSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Contract Types"],
        summary="Lister les types de contrat",
        description="Liste de tous les types de contrat.",
    ),
    retrieve=extend_schema(
        tags=["Contract Types"],
        summary="Détail d’un type de contrat",
    ),
    create=extend_schema(
        tags=["Contract Types"],
        summary="Créer un type de contrat",
    ),
    update=extend_schema(
        tags=["Contract Types"],
        summary="Mettre à jour un type de contrat",
    ),
    partial_update=extend_schema(
        tags=["Contract Types"],
        summary="Mettre à jour partiellement un type de contrat",
    ),
    destroy=extend_schema(
        tags=["Contract Types"],
        summary="Supprimer un type de contrat",
    ),
)
class ContractTypeViewSet(ModelViewSet):
    """
    CRUD des types de contrat.
    """

    queryset = ContractType.objects.all()
    serializer_class = ContractTypeSerializer
