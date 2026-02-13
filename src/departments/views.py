from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import Department
from .serializers import DepartmentSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Departments"],
        summary="Lister les départements",
        description="Liste de tous les départements.",
    ),
    retrieve=extend_schema(
        tags=["Departments"],
        summary="Détail d’un département",
    ),
    create=extend_schema(
        tags=["Departments"],
        summary="Créer un département",
    ),
    update=extend_schema(
        tags=["Departments"],
        summary="Mettre à jour un département",
    ),
    partial_update=extend_schema(
        tags=["Departments"],
        summary="Mettre à jour partiellement un département",
    ),
    destroy=extend_schema(
        tags=["Departments"],
        summary="Supprimer un département",
    ),
)
class DepartmentViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = DepartmentSerializer

    queryset = Department.objects.select_related("director").all()

    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = [
        "name",
        "description",
        "director__first_name",
        "director__last_name",
        "director__email",
    ]
    ordering_fields = ["created_at", "updated_at", "name", "is_active"]
    ordering = ["-created_at"]
