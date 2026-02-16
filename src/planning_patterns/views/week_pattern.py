from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from planning_patterns.models import WeekPattern
from planning_patterns.serializers.week_pattern import WeekPatternSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Week Patterns"],
        summary="Lister les semaines types",
        description="Liste de toutes les semaines types.",
    ),
    retrieve=extend_schema(
        tags=["Week Patterns"],
        summary="Détail d’une semaine type",
    ),
    create=extend_schema(
        tags=["Week Patterns"],
        summary="Créer une semaine type",
    ),
    update=extend_schema(
        tags=["Week Patterns"],
        summary="Mettre à jour une semaine type",
    ),
    partial_update=extend_schema(
        tags=["Week Patterns"],
        summary="Mettre à jour partiellement une semaine type",
    ),
    destroy=extend_schema(
        tags=["Week Patterns"],
        summary="Supprimer une semaine type",
    ),
)
class WeekPatternViewSet(ModelViewSet):
    """
    CRUD des semaines types.
    """

    queryset = WeekPattern.objects.prefetch_related("time_slots").all()
    serializer_class = WeekPatternSerializer
