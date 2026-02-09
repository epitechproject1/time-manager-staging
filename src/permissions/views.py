from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from .models import Permission
from .permissions import IsAdminOrPermissionManager
from .serializers import (
    PermissionCreateSerializer,
    PermissionSerializer,
    PermissionUpdateSerializer,
)


@extend_schema_view(
    list=extend_schema(
        tags=["Permissions"],
        summary="Lister les permissions",
        description="Liste des permissions visibles par l'utilisateur.",
    ),
    retrieve=extend_schema(
        tags=["Permissions"],
        summary="Détail d’une permission",
    ),
    create=extend_schema(
        tags=["Permissions"],
        summary="Créer une permission",
    ),
    update=extend_schema(
        tags=["Permissions"],
        summary="Mettre à jour une permission",
    ),
    partial_update=extend_schema(
        tags=["Permissions"],
        summary="Mettre à jour partiellement une permission",
    ),
    destroy=extend_schema(
        tags=["Permissions"],
        summary="Supprimer une permission",
    ),
)
class PermissionViewSet(ModelViewSet):
    """
    API CRUD des permissions.

    Règles d'accès :
    - Lecture : utilisateur authentifié
    - Création / modification / suppression :
      ADMIN ou utilisateur autorisé à gérer les permissions
    """

    queryset = Permission.objects.select_related(
        "granted_by_user",
        "granted_to_user",
    ).order_by("-created_at")

    permission_classes = [
        IsAuthenticated,
        IsAdminOrPermissionManager,
    ]

    def get_serializer_class(self):
        if self.action == "create":
            return PermissionCreateSerializer

        if self.action in ("update", "partial_update"):
            return PermissionUpdateSerializer

        return PermissionSerializer

    def get_queryset(self):
        """
        Un utilisateur ne peut voir que :
        - les permissions qu'il a reçues
        - les permissions qu'il a accordées
        - toutes les permissions s'il est ADMIN
        """
        user = self.request.user

        if user.is_superuser or user.role == "ADMIN":
            return self.queryset

        return self.queryset.filter(granted_to_user=user) | self.queryset.filter(
            granted_by_user=user
        )
