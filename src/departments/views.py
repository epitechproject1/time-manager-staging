from drf_spectacular.utils import extend_schema, extend_schema_view
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
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
