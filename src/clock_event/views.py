from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from shift.models import Shift

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

    ⚠️  La validation du pointage se fait via clock_validation.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ClockEventSerializer

    def get_queryset(self):
        return (
            ClockEvent.objects.filter(user=self.request.user)
            .select_related("user", "shift")
            .order_by("-timestamp")
        )

    # ─────────────────────────────
    # CLOCK IN
    # ─────────────────────────────
    @action(detail=False, methods=["post"], url_path="clock-in")
    def clock_in(self, request):
        """
        Crée un ClockEvent CLOCK_IN en PENDING.
        Retourne le ClockValidationCode généré automatiquement (code + expiration).
        """
        serializer = ClockInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        shift = Shift.objects.get(pk=serializer.validated_data["shift_id"])

        event = ClockEvent.objects.create(
            user=request.user,
            shift=shift,
            event_type=ClockEvent.EventType.CLOCK_IN,
            timestamp=timezone.now(),
        )

        # Création du code de validation — délégué au module clock_validation
        from clock_validation.models import ClockValidationCode
        from clock_validation.serializers import ClockValidationCodeSerializer

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
        """
        Crée un ClockEvent CLOCK_OUT en PENDING.
        Retourne le ClockValidationCode généré automatiquement (code + expiration).
        """
        serializer = ClockOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        shift = Shift.objects.get(pk=serializer.validated_data["shift_id"])

        event = ClockEvent.objects.create(
            user=request.user,
            shift=shift,
            event_type=ClockEvent.EventType.CLOCK_OUT,
            timestamp=timezone.now(),
        )

        from clock_validation.models import ClockValidationCode
        from clock_validation.serializers import ClockValidationCodeSerializer

        validation = ClockValidationCode.create_for_event(event)

        return Response(
            ClockValidationCodeSerializer(validation).data,
            status=status.HTTP_201_CREATED,
        )
