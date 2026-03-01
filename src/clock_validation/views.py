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
    """
    Gestion de la validation des pointages via code.

    POST /clock-validation/submit/ → soumettre un code
    GET  /clock-validation/{id}/   → consulter un code
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ClockValidationCodeSerializer

    # ─────────────────────────────
    # QUERYSET
    # ─────────────────────────────
    def get_queryset(self):
        return ClockValidationCode.objects.filter(
            clock_event__user=self.request.user
        ).select_related("clock_event__user", "clock_event__shift")

    # ─────────────────────────────
    # SUBMIT CODE
    # ─────────────────────────────
    @action(detail=False, methods=["post"], url_path="submit")
    def submit(self, request):
        """
        L'utilisateur soumet le code reçu par email.

        200 → code valide, ClockEvent approuvé
        400 → code invalide ou expiré
        """

        serializer = SubmitCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validation = serializer.validated_data["validation"]
        submitted_code = serializer.validated_data["code"]

        success = validation.verify(submitted_code)

        # 🔄 rafraîchir pour récupérer statuts à jour
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
