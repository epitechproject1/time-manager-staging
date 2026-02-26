from rest_framework.permissions import SAFE_METHODS, BasePermission

from users.constants import UserRole


class IsAdminOrReadOnlyTeamsDirectory(BasePermission):
    """
    ADMIN:
      - accès total (CRUD)

    USER/DIRECTOR:
      - lecture uniquement (GET/HEAD/OPTIONS)
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.role == UserRole.ADMIN:
            return True

        return request.method in SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        if request.user.role == UserRole.ADMIN:
            return True
        return request.method in SAFE_METHODS
