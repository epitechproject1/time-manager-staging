from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
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
    queryset = Shift.objects.select_related(
        "user", "assignment", "assignment__week_pattern"
    )

    serializer_class = ShiftSerializer
    pagination_class = ShiftPagination

    filter_backends = [SearchFilter]
    search_fields = [
        "user__first_name",
        "user__last_name",
        "assignment__week_pattern__name",
    ]
