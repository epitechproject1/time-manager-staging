from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets

from .models import Clock
from .serializers import ClockSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Clocks"],
        summary="Lister tous les pointages",
    ),
    retrieve=extend_schema(
        tags=["Clocks"],
        summary="Détail d’un pointage",
    ),
    create=extend_schema(
        tags=["Clocks"],
        summary="Créer un nouveau pointage",
    ),
    update=extend_schema(
        tags=["Clocks"],
        summary="Mettre à jour un pointage",
    ),
    partial_update=extend_schema(
        tags=["Clocks"],
        summary="Mettre à jour partiellement un pointage",
    ),
    destroy=extend_schema(
        tags=["Clocks"],
        summary="Supprimer un pointage",
    ),
)
class ClockViewSet(viewsets.ModelViewSet):
    queryset = Clock.objects.all()
    serializer_class = ClockSerializer
    permission_classes = [permissions.IsAuthenticated]
