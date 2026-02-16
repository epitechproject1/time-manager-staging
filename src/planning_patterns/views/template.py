from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from planning_patterns.models import PlanningTemplate
from planning_patterns.serializers.template import PlanningTemplateSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Planning Templates"],
        summary="Lister les templates",
        description="Liste de tous les templates de planning.",
    ),
    retrieve=extend_schema(
        tags=["Planning Templates"],
        summary="Détail d’un template",
    ),
    create=extend_schema(
        tags=["Planning Templates"],
        summary="Créer un template",
    ),
    update=extend_schema(
        tags=["Planning Templates"],
        summary="Mettre à jour un template",
    ),
    partial_update=extend_schema(
        tags=["Planning Templates"],
        summary="Mettre à jour partiellement un template",
    ),
    destroy=extend_schema(
        tags=["Planning Templates"],
        summary="Supprimer un template",
    ),
)
class PlanningTemplateViewSet(ModelViewSet):
    """
    CRUD des templates de planning.
    """

    queryset = PlanningTemplate.objects.select_related("week_pattern").all()
    serializer_class = PlanningTemplateSerializer
