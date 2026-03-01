from rest_framework.permissions import BasePermission

from .constants import UserRole


class IsAdminOrOwnerProfile(BasePermission):
    """
    ADMIN / MANAGER : accès total

    USER :
        - peut retrieve / update / partial_update / destroy son propre profil
        - ne peut pas accéder à la liste
        - ne peut pas créer
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # ✅ Admin et Manager -> accès total
        if request.user.role in [UserRole.ADMIN, UserRole.MANAGER]:
            return True

        # ❌ USER → pas accès à la liste
        if view.action == "list":
            return False

        # USER → accès à ses actions perso
        if view.action in ["retrieve", "update", "partial_update", "destroy"]:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        # ✅ Admin / Manager → accès total
        if request.user.role in [UserRole.ADMIN, UserRole.MANAGER]:
            return True

        # USER → uniquement son propre profil
        return obj == request.user
