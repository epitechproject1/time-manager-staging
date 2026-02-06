from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import User
from .permissions import IsAdminForCreateOtherwiseReadOnly
from .serializers import (
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)

@extend_schema_view(
    list=extend_schema(
        tags=["Users"],
        summary="Lister les utilisateurs",
    ),
    retrieve=extend_schema(
        tags=["Users"],
        summary="Détail d’un utilisateur",
    ),
    create=extend_schema(
        tags=["Users"],
        summary="Créer un utilisateur",
    ),
    update=extend_schema(
        tags=["Users"],
        summary="Mettre à jour un utilisateur",
    ),
    partial_update=extend_schema(
        tags=["Users"],
        summary="Mettre à jour partiellement un utilisateur",
    ),
    destroy=extend_schema(
        tags=["Users"],
        summary="Supprimer un utilisateur",
    ),
)
class UserViewSet(ModelViewSet):
    """
    API CRUD des utilisateurs.

    Permissions :
    - Lecture : utilisateurs authentifiés
    - Création / modification / suppression : ADMIN uniquement
    """

    queryset = User.objects.all().order_by("-created_at")
    permission_classes = [IsAdminForCreateOtherwiseReadOnly]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer

        if self.action in ("update", "partial_update"):
            return UserUpdateSerializer

        return UserSerializer