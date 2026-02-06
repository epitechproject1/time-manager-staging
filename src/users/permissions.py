from rest_framework.permissions import BasePermission, SAFE_METHODS

from .constants import UserRole


class IsAdminForCreateOtherwiseReadOnly(BasePermission):
    """
    - Lecture (GET, HEAD, OPTIONS) : utilisateurs authentifiés
    - Création (POST) : ADMIN uniquement
    - Modification / suppression : ADMIN uniquement
    """

    def has_permission(self, request, view):
        # Lecture autorisée aux utilisateurs authentifiés
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated

        # Création, modification, suppression réservées aux ADMIN
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == UserRole.ADMIN
        )