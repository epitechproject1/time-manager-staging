from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from clock_event.serializers import ClockEventSerializer

from .models import ClockValidationCode
from .serializers import ClockValidationCodeSerializer, SubmitCodeSerializer


class ClockValidationViewSet(
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):

    permission_classes = [IsAuthenticated]
    serializer_class = ClockValidationCodeSerializer

    def get_queryset(self):
        return ClockValidationCode.objects.filter(
            clock_event__user=self.request.user
        ).select_related("clock_event__user", "clock_event__shift")

    # ─────────────────────────────
    # SUBMIT
    # ─────────────────────────────
    @action(detail=False, methods=["post"], url_path="submit")
    def submit(self, request):
        """
        L'employé soumet le code à 6 chiffres reçu après son pointage.

        Recherche le dernier code PENDING de l'utilisateur connecté.
        Délègue la vérification à ClockValidationCode.verify().

        Réponses :
          200 → code valide, ClockEvent approuvé
          400 → code invalide ou expiré, ClockEvent rejeté
          404 → aucun code en attente trouvé
        """
        serializer = SubmitCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        submitted_code = serializer.validated_data["code"]

        validation = (
            ClockValidationCode.objects.filter(
                clock_event__user=request.user,
                status=ClockValidationCode.Status.PENDING,
            )
            .select_related("clock_event__user", "clock_event__shift")
            .order_by("-created_at")
            .first()
        )

        if not validation:
            return Response(
                {"detail": "Aucun code en attente."},
                status=status.HTTP_404_NOT_FOUND,
            )

        success = validation.verify(submitted_code)

        # Recharge les instances pour avoir les statuts à jour en DB
        validation.refresh_from_db()
        validation.clock_event.refresh_from_db()

        response_data = {
            "success": success,
            "event": ClockEventSerializer(validation.clock_event).data,
        }

        if not success:
            response_data["detail"] = (
                validation.clock_event.note or "Code invalide ou expiré."
            )
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        return Response(response_data, status=status.HTTP_200_OK)
