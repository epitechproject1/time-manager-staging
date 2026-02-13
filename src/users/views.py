from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from notifications.services import send_welcome_email
from notifications.utils import run_async

from .constants import UserRole
from .models import User
from .permissions import IsAdminOrOwnerProfile
from .serializers import UserCreateSerializer, UserSerializer, UserUpdateSerializer


@extend_schema_view(
    list=extend_schema(tags=["Users"], summary="Lister les utilisateurs"),
    retrieve=extend_schema(tags=["Users"], summary="Détail d’un utilisateur"),
    create=extend_schema(tags=["Users"], summary="Créer un utilisateur"),
    update=extend_schema(tags=["Users"], summary="Mettre à jour un utilisateur"),
    partial_update=extend_schema(
        tags=["Users"], summary="Mettre à jour partiellement un utilisateur"
    ),
    destroy=extend_schema(tags=["Users"], summary="Supprimer un utilisateur"),
)
class UserViewSet(ModelViewSet):
    permission_classes = [IsAdminOrOwnerProfile]

    def get_queryset(self):
        user = self.request.user

        if user.role == UserRole.ADMIN:
            return User.objects.all().order_by("-created_at")

        return User.objects.filter(id=user.id)

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer

        if self.action in ("update", "partial_update"):
            return UserUpdateSerializer

        return UserSerializer

    def perform_create(self, serializer):
        """
        Création utilisateur + envoi email async
        """
        user = serializer.save()

        # ⚠️ IMPORTANT : récupérer le mot de passe envoyé dans la request
        raw_password = self.request.data.get("password")

        if raw_password:
            run_async(send_welcome_email, user, raw_password)

    @extend_schema(summary="Récupérer le profil de l'utilisateur connecté")
    @action(
        detail=False,
        methods=["get"],
        url_path="me",
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
