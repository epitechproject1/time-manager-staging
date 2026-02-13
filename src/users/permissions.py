from rest_framework.permissions import BasePermission

from .constants import UserRole


class IsAdminOrOwnerProfile(BasePermission):
    """
    ADMIN : accès total

    USER :
        - peut retrieve / update / partial_update / destroy son propre profil
        - ne peut pas accéder à la liste
        - ne peut pas créer
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Admin -> accès total
        if request.user.role == UserRole.ADMIN:
            return True

        # Interdire la liste
        if view.action == "list":
            return False

        # Autoriser ces actions (contrôle final fait dans has_object_permission)
        if view.action in ["retrieve", "update", "partial_update", "destroy"]:
            return True

        # Interdire create
        return False

    def has_object_permission(self, request, view, obj):
        # Admin -> accès total
        if request.user.role == UserRole.ADMIN:
            return True

        # L'utilisateur peut agir uniquement sur lui-même
        return obj == request.user
