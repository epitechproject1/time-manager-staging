from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.exceptions import PermissionDenied
from users.constants import UserRole


class IsAdminOrReadOnlyDepartmentsDirectory(BasePermission):
    """
    ADMIN   : accès total (CRUD + stats + export + import)
    MANAGER : lecture + export scopé (csv/pdf) + stats scopées
    DIRECTOR: lecture + export scopé (csv/pdf)
    USER    : lecture uniquement
    """

    DIRECTOR_ALLOWED_ACTIONS = {"export_csv", "export_pdf"}
    MANAGER_ALLOWED_ACTIONS  = {"export_csv", "export_pdf", "stats"}
    ADMIN_ONLY_ACTIONS       = {"export_xlsx", "import_csv"}

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            raise PermissionDenied("Authentification requise.")

        role   = getattr(user, "role", None)
        action = getattr(view, "action", None)

        # ── ADMIN : tout est autorisé ─────────────────────────────────────
        if role == UserRole.ADMIN:
            return True

        # ── Toute méthode safe (GET/HEAD/OPTIONS) ─────────────────────────
        if request.method in SAFE_METHODS:
            if action in self.ADMIN_ONLY_ACTIONS:
                raise PermissionDenied("Accès réservé à l'administrateur.")
            return True

        # ── Méthodes non-safe : vérification par rôle ─────────────────────

        # Refus immédiat sur les actions admin-only, peu importe le rôle
        if action in self.ADMIN_ONLY_ACTIONS:
            raise PermissionDenied("Accès réservé à l'administrateur.")

        # DIRECTOR (si le rôle existe dans l'enum)
        director_role = getattr(UserRole, "DIRECTOR", None)
        if director_role is not None and role == director_role:
            if action in self.DIRECTOR_ALLOWED_ACTIONS:
                return True
            raise PermissionDenied("Accès refusé pour ce rôle.")

        # MANAGER (si le rôle existe dans l'enum)
        manager_role = getattr(UserRole, "MANAGER", None)
        if manager_role is not None and role == manager_role:
            if action in self.MANAGER_ALLOWED_ACTIONS:
                return True
            raise PermissionDenied("Accès refusé pour ce rôle.")

        # USER ou tout autre rôle non reconnu
        raise PermissionDenied(
            "Vous n'avez pas le droit de modifier des départements selon votre poste."
        )

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)