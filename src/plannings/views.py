from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from .models import Planning
from .serializers import PlanningSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Plannings"],
        summary="Lister les plannings",
        description="Liste de tous les plannings.",
    ),
    retrieve=extend_schema(
        tags=["Plannings"],
        summary="Détail d’un planning",
    ),
    create=extend_schema(
        tags=["Plannings"],
        summary="Créer un planning",
    ),
    update=extend_schema(
        tags=["Plannings"],
        summary="Mettre à jour un planning",
    ),
    partial_update=extend_schema(
        tags=["Plannings"],
        summary="Mettre à jour partiellement un planning",
    ),
    destroy=extend_schema(
        tags=["Plannings"],
        summary="Supprimer un planning",
    ),
)
class PlanningViewSet(ModelViewSet):
    queryset = Planning.objects.all()
    serializer_class = PlanningSerializer
    permission_classes = [AllowAny]
