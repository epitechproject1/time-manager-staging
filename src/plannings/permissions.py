from rest_framework.permissions import SAFE_METHODS, BasePermission

from users.constants import UserRole


class IsAdminOrOwner(BasePermission):
    """
    - Admin: accès total
    - User: accès uniquement à ses plannings
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin => ok
        if request.user.role == UserRole.ADMIN:
            return True

        # Lecture ok si owner
        if request.method in SAFE_METHODS:
            return obj.user_id == request.user.id

        # Écriture ok si owner
        return obj.user_id == request.user.id
