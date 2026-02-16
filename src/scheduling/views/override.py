from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from scheduling.models import ShiftOverride
from scheduling.serializers.override import ShiftOverrideSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Shift Overrides"],
        summary="Lister les exceptions",
        description="Liste des modifications ponctuelles de shifts.",
    ),
    retrieve=extend_schema(
        tags=["Shift Overrides"],
        summary="Détail d’une exception",
    ),
    create=extend_schema(
        tags=["Shift Overrides"],
        summary="Créer une exception",
    ),
    update=extend_schema(
        tags=["Shift Overrides"],
        summary="Mettre à jour une exception",
    ),
    partial_update=extend_schema(
        tags=["Shift Overrides"],
        summary="Mettre à jour partiellement une exception",
    ),
    destroy=extend_schema(
        tags=["Shift Overrides"],
        summary="Supprimer une exception",
    ),
)
class ShiftOverrideViewSet(ModelViewSet):
    """
    CRUD des exceptions de planning.
    """

    queryset = ShiftOverride.objects.select_related("shift").all()
    serializer_class = ShiftOverrideSerializer
