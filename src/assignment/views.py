from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from assignment.models import ScheduleAssignment
from assignment.serializers import ScheduleAssignmentSerializer
from assignment.services import generate_shifts_for_assignment


class ScheduleAssignmentPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


@extend_schema_view(
    list=extend_schema(
        tags=["Schedule Assignments"],
        summary="Lister les affectations",
        description="Liste des plannings assignés aux contrats.",
    ),
    retrieve=extend_schema(tags=["Schedule Assignments"]),
    create=extend_schema(tags=["Schedule Assignments"]),
    update=extend_schema(tags=["Schedule Assignments"]),
    partial_update=extend_schema(tags=["Schedule Assignments"]),
    destroy=extend_schema(tags=["Schedule Assignments"]),
)
class ScheduleAssignmentViewSet(ModelViewSet):
    queryset = ScheduleAssignment.objects.select_related(
        "contract",
        "week_pattern",
        "contract__user",
    )

    serializer_class = ScheduleAssignmentSerializer
    pagination_class = ScheduleAssignmentPagination

    filter_backends = [SearchFilter]
    search_fields = [
        "contract__user__first_name",
        "contract__user__last_name",
        "week_pattern__name",
    ]

    @extend_schema(
        tags=["Schedule Assignments"],
        summary="Générer les shifts",
        description=(
            "Génère les shifts pour cet assignment en fonction "
            "du week pattern et de la période. "
            "Par défaut, les jours fériés français sont exclus."
        ),
        request=None,
        responses={200: None},
    )
    @action(detail=True, methods=["post"], url_path="generate-shifts")
    def generate_shifts(self, request, pk=None):
        assignment = self.get_object()

        include_holidays = request.data.get("include_holidays", False)

        created_shifts = generate_shifts_for_assignment(
            assignment,
            include_holidays=include_holidays,
        )

        return Response(
            {
                "assignment_id": assignment.id,
                "created_shifts": len(created_shifts),
                "include_holidays": include_holidays,
            },
            status=status.HTTP_200_OK,
        )
