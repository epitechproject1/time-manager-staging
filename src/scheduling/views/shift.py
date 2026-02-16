from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from scheduling.models import Shift
from scheduling.serializers.shift import ShiftSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Shifts"],
        summary="Lister les shifts",
        description="Liste des occurrences réelles du planning.",
    ),
    retrieve=extend_schema(
        tags=["Shifts"],
        summary="Détail d’un shift",
    ),
    create=extend_schema(
        tags=["Shifts"],
        summary="Créer un shift",
    ),
    update=extend_schema(
        tags=["Shifts"],
        summary="Mettre à jour un shift",
    ),
    partial_update=extend_schema(
        tags=["Shifts"],
        summary="Mettre à jour partiellement un shift",
    ),
    destroy=extend_schema(
        tags=["Shifts"],
        summary="Supprimer un shift",
    ),
)
class ShiftViewSet(ModelViewSet):
    """
    CRUD des occurrences réelles.
    """

    queryset = Shift.objects.select_related(
        "user", "assignment", "assignment__contract"
    ).all()

    serializer_class = ShiftSerializer
