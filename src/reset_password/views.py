from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer,
)
from .services import create_and_send_reset_code, verify_reset_code

User = get_user_model()


# =========================
# REQUEST RESET
# =========================
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Authentication"],
        summary="Demander un code de réinitialisation",
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        user = User.objects.filter(email=email).first()
        if user:
            create_and_send_reset_code(user)

        # réponse neutre pour éviter user enumeration
        return Response(
            {"detail": "Si cet email existe, un code a été envoyé."},
            status=status.HTTP_200_OK,
        )


# =========================
# VERIFY CODE
# =========================
class PasswordResetVerifyView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Authentication"],
        summary="Vérifier le code de réinitialisation",
    )
    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"valid": False}, status=status.HTTP_200_OK)

        reset = verify_reset_code(user, code)
        if not reset:
            return Response({"valid": False}, status=status.HTTP_200_OK)

        return Response({"valid": True}, status=status.HTTP_200_OK)


# =========================
# CONFIRM RESET PASSWORD
# =========================
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Authentication"],
        summary="Confirmer la réinitialisation du mot de passe",
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]
        new_password = serializer.validated_data["new_password"]

        user = User.objects.filter(email=email).first()
        if not user:
            return Response(
                {"detail": "Code invalide ou expiré"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reset = verify_reset_code(user, code)
        if not reset:
            return Response(
                {"detail": "Code invalide ou expiré"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 🔐 hash du nouveau mot de passe
        user.set_password(new_password)
        user.save()

        # 🔒 code inutilisable après usage
        reset.is_used = True
        reset.save()

        return Response(
            {"detail": "Mot de passe réinitialisé avec succès"},
            status=status.HTTP_200_OK,
        )
