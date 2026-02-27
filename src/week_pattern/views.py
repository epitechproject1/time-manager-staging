from django.db.models import ProtectedError
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from week_pattern.models import WeekPattern
from week_pattern.serializers import WeekPatternSerializer


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

    # Capture propre des erreurs de suppression protégée
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        try:
            self.perform_destroy(instance)
        except ProtectedError as e:
            # 👉 Optionnel : compter les objets liés
            related_objects = len(e.protected_objects)

            return Response(
                {
                    "detail": "Impossible de supprimer cette semaine ",
                    "protected_objects_count": related_objects,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)
