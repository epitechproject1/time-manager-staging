from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from scheduling.models import ScheduleAssignment
from scheduling.serializers.assignment import ScheduleAssignmentSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Schedule Assignments"],
        summary="Lister les affectations",
        description="Liste des plannings assignés aux contrats.",
    ),
    retrieve=extend_schema(
        tags=["Schedule Assignments"],
        summary="Détail d’une affectation",
    ),
    create=extend_schema(
        tags=["Schedule Assignments"],
        summary="Créer une affectation",
    ),
    update=extend_schema(
        tags=["Schedule Assignments"],
        summary="Mettre à jour une affectation",
    ),
    partial_update=extend_schema(
        tags=["Schedule Assignments"],
        summary="Mettre à jour partiellement une affectation",
    ),
    destroy=extend_schema(
        tags=["Schedule Assignments"],
        summary="Supprimer une affectation",
    ),
)
class ScheduleAssignmentViewSet(ModelViewSet):
    """
    CRUD des affectations de planning.
    """

    queryset = ScheduleAssignment.objects.select_related(
        "contract", "week_pattern", "contract__user"
    ).all()

    serializer_class = ScheduleAssignmentSerializer
