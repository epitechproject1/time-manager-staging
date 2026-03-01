from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS, BasePermission

from users.constants import UserRole


class IsAdminOrReadOnlyTeamsDirectory(BasePermission):
    """
    ADMIN: accès total (CRUD + stats + export + import)
    DIRECTOR (si existe): lecture + import_csv uniquement
    MANAGER (si existe): lecture + export_csv/export_pdf uniquement
    USER: lecture uniquement
    """

    DIRECTOR_ALLOWED_ACTIONS = {"import_csv"}
    MANAGER_ALLOWED_ACTIONS = {"export_csv", "export_pdf"}

    # ✅ reste admin-only (manager/director interdits)
    ADMIN_ONLY_ACTIONS = {"stats", "export_xlsx"}

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            raise PermissionDenied("Authentification requise.")

        action = getattr(view, "action", None)

        # ✅ Admin = tout
        if getattr(user, "role", None) == UserRole.ADMIN:
            return True

        # ✅ Director (si existe)
        director_role = getattr(UserRole, "DIRECTOR", None)
        if director_role and getattr(user, "role", None) == director_role:
            if request.method in SAFE_METHODS:
                return True
            if action in self.DIRECTOR_ALLOWED_ACTIONS:
                return True
            raise PermissionDenied("Accès refusé pour ce rôle.")

        # ✅ Manager (si existe)
        manager_role = getattr(UserRole, "MANAGER", None)
        if manager_role and getattr(user, "role", None) == manager_role:
            if request.method in SAFE_METHODS:
                return True
            if action in self.MANAGER_ALLOWED_ACTIONS:
                return True
            raise PermissionDenied("Accès refusé pour ce rôle.")

        # ✅ Non-admin: stats / export_xlsx interdits
        if action in self.ADMIN_ONLY_ACTIONS:
            raise PermissionDenied("Accès réservé à l'administrateur.")

        # ✅ Lecture OK
        if request.method in SAFE_METHODS:
            return True

        raise PermissionDenied(
            "Vous n’avez pas le droit de modifier des équipes selon votre poste."
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
