from rest_framework.permissions import SAFE_METHODS, BasePermission

from users.constants import UserRole


class IsAdminOrPermissionManager(BasePermission):
    """
    - Lecture (GET, HEAD, OPTIONS) : utilisateurs authentifiés
    - Création / modification / suppression : ADMIN uniquement
    """

    def has_permission(self, request, view):
        # Lecture autorisée uniquement aux utilisateurs authentifiés
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Écriture réservée aux ADMIN
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.ADMIN
        )
