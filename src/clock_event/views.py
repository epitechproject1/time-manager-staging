from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from clock_validation.models import ClockValidationCode
from clock_validation.serializers import ClockValidationCodeSerializer

from .models import ClockEvent
from .serializers import ClockEventSerializer, ClockInSerializer, ClockOutSerializer


class ClockEventViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Gestion des pointages utilisateur.

    GET  /clock-events/           → historique des pointages
    GET  /clock-events/{id}/      → détail d'un pointage
    POST /clock-events/clock-in/  → pointer le début d'un shift
    POST /clock-events/clock-out/ → pointer la fin d'un shift
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ClockEventSerializer

    # ─────────────────────────────
    # QUERYSET
    # ─────────────────────────────
    def get_queryset(self):
        return (
            ClockEvent.objects.filter(user=self.request.user)
            .select_related("user", "shift")
            .order_by("-timestamp")
        )

    # ─────────────────────────────
    # SERIALIZER DYNAMIQUE
    # ─────────────────────────────
    def get_serializer_class(self):
        if self.action == "clock_in":
            return ClockInSerializer
        if self.action == "clock_out":
            return ClockOutSerializer
        return ClockEventSerializer

    # ─────────────────────────────
    # CLOCK IN
    # ─────────────────────────────
    @action(detail=False, methods=["post"], url_path="clock-in")
    def clock_in(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        shift = serializer.validated_data["shift"]

        event = ClockEvent.objects.create(
            user=request.user,
            shift=shift,
            event_type=ClockEvent.EventType.CLOCK_IN,
            timestamp=timezone.now(),
        )

        validation = ClockValidationCode.create_for_event(event)

        return Response(
            ClockValidationCodeSerializer(validation).data,
            status=status.HTTP_201_CREATED,
        )

    # ─────────────────────────────
    # CLOCK OUT
    # ─────────────────────────────
    @action(detail=False, methods=["post"], url_path="clock-out")
    def clock_out(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        shift = serializer.validated_data["shift"]

        event = ClockEvent.objects.create(
            user=request.user,
            shift=shift,
            event_type=ClockEvent.EventType.CLOCK_OUT,
            timestamp=timezone.now(),
        )

        validation = ClockValidationCode.create_for_event(event)

        return Response(
            ClockValidationCodeSerializer(validation).data,
            status=status.HTTP_201_CREATED,
        )
