from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from shift.models import Shift
from shift.serializers import ShiftSerializer


class ShiftPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


@extend_schema_view(
    list=extend_schema(tags=["Shifts"], summary="Lister les shifts"),
    retrieve=extend_schema(tags=["Shifts"]),
    create=extend_schema(tags=["Shifts"]),
    update=extend_schema(tags=["Shifts"]),
    partial_update=extend_schema(tags=["Shifts"]),
    destroy=extend_schema(tags=["Shifts"]),
)
class ShiftViewSet(ModelViewSet):
    """
    API des occurrences réelles de planning.

    Inclut le statut de pointage (clock_status)
    via le ShiftSerializer.
    """

    queryset = Shift.objects.select_related(
        "user",
        "assignment",
        "assignment__week_pattern",
    ).prefetch_related(
        "clock_events"
    )  # 🔥 important

    serializer_class = ShiftSerializer
    pagination_class = ShiftPagination

    filter_backends = [SearchFilter]
    search_fields = [
        "user__first_name",
        "user__last_name",
        "assignment__week_pattern__name",
    ]

    # ─────────────────────────────
    # SHIFTS DE L'UTILISATEUR CONNECTÉ
    # ─────────────────────────────
    @action(detail=False, methods=["get"], url_path="me")
    def my_shifts(self, request):
        """
        Retourne les shifts de l'utilisateur connecté
        avec leur statut de pointage.
        """

        queryset = self.get_queryset().filter(user=request.user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
