from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.viewsets import ModelViewSet

from time_slot_pattern.models import TimeSlotPattern
from time_slot_pattern.serializers import TimeSlotPatternSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Time Slot Patterns"],
        summary="Lister les créneaux",
        description="Liste de tous les créneaux de semaine type.",
    ),
    retrieve=extend_schema(
        tags=["Time Slot Patterns"],
        summary="Détail d’un créneau",
    ),
    create=extend_schema(
        tags=["Time Slot Patterns"],
        summary="Créer un créneau",
    ),
    update=extend_schema(
        tags=["Time Slot Patterns"],
        summary="Mettre à jour un créneau",
    ),
    partial_update=extend_schema(
        tags=["Time Slot Patterns"],
        summary="Mettre à jour partiellement un créneau",
    ),
    destroy=extend_schema(
        tags=["Time Slot Patterns"],
        summary="Supprimer un créneau",
    ),
)
class TimeSlotPatternViewSet(ModelViewSet):
    queryset = TimeSlotPattern.objects.select_related("week_pattern")
    serializer_class = TimeSlotPatternSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["week_pattern", "weekday", "slot_type"]
