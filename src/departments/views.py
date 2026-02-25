import logging
from datetime import datetime

from django.core.cache import cache
from django.db.models import Case, Count, IntegerField, Q, Sum, Value, When
from django.db.models.functions import Lower
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from teams.models import Teams
from teams.serializers import TeamsLiteSerializer
from users.constants import UserRole

from .models import Department
from .permissions import IsAdminOrReadOnlyDepartmentsDirectory
from .serializers import DepartmentLiteSerializer, DepartmentSerializer

logger = logging.getLogger(__name__)
DEPARTMENTS_CACHE_PATTERN = "departments:*"

VALID_ORDERINGS = {
    "name",
    "-name",
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
    "teams_count",
    "-teams_count",
    "employees_count",
    "-employees_count",
}


def safe_cache_delete_pattern(pattern: str) -> None:
    try:
        delete_pattern = getattr(cache, "delete_pattern", None)
        if callable(delete_pattern):
            delete_pattern(pattern)
        else:
            logger.warning(
                "Cache backend ne supporte pas delete_pattern(). Pattern ignoré: %s",
                pattern,
            )
    except Exception:
        logger.exception("Erreur lors de la suppression du cache pattern: %s", pattern)


def _build_count_annotations():
    teams_counts = {
        row["department_id"]: row["c"]
        for row in Teams.objects.values("department_id").annotate(c=Count("id"))
    }
    employees_counts = {
        row["department_id"]: row["c"]
        for row in Teams.objects.values("department_id").annotate(
            c=Count("members", distinct=True)
        )
    }

    teams_whens = [When(pk=pk, then=c) for pk, c in teams_counts.items()]
    employees_whens = [When(pk=pk, then=c) for pk, c in employees_counts.items()]

    return (
        (
            Case(*teams_whens, default=0, output_field=IntegerField())
            if teams_whens
            else Case(default=0, output_field=IntegerField())
        ),
        (
            Case(*employees_whens, default=0, output_field=IntegerField())
            if employees_whens
            else Case(default=0, output_field=IntegerField())
        ),
    )


@extend_schema_view(
    list=extend_schema(
        tags=["Departments"],
        summary="Lister les départements",
        description="Récupère la liste des départements avec recherche, filtres et tri",
        parameters=[
            OpenApiParameter(
                name="q", description="Recherche", required=False, type=str
            ),
            OpenApiParameter(
                name="is_active", description="Statut", required=False, type=bool
            ),
            OpenApiParameter(
                name="director_id", description="Directeur", required=False, type=int
            ),
            OpenApiParameter(
                name="my_departments",
                description="Mes départements",
                required=False,
                type=bool,
            ),
            OpenApiParameter(
                name="ordering", description="Tri", required=False, type=str
            ),
        ],
    ),
    retrieve=extend_schema(tags=["Departments"], summary="Détail d'un département"),
    create=extend_schema(tags=["Departments"], summary="Créer un département"),
    update=extend_schema(tags=["Departments"], summary="Mettre à jour un département"),
    partial_update=extend_schema(tags=["Departments"], summary="Mise à jour partielle"),
    destroy=extend_schema(tags=["Departments"], summary="Supprimer un département"),
)
class DepartmentViewSet(ModelViewSet):
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnlyDepartmentsDirectory]
    filter_backends = [OrderingFilter]
    ordering_fields = [
        "name",
        "created_at",
        "updated_at",
        "teams_count",
        "employees_count",
    ]
    ordering = ["-created_at"]

    def _is_scoped_department(self, dept: Department) -> bool:
        user = self.request.user
        if user.role == UserRole.ADMIN:
            return True
        if dept.director_id == user.id:
            return True
        return Teams.objects.filter(department=dept, members=user).exists()

    def get_serializer_class(self):
        if self.action in ("list", "search"):
            return DepartmentLiteSerializer

        if self.action == "retrieve":
            dept = self.get_object()
            return (
                DepartmentSerializer
                if self._is_scoped_department(dept)
                else DepartmentLiteSerializer
            )

        if self.action == "my_departments":
            return DepartmentSerializer

        return DepartmentSerializer

    def get_queryset(self):
        teams_count_ann, employees_count_ann = _build_count_annotations()

        qs = (
            Department.objects.all()
            .select_related("director")
            .annotate(
                teams_count=teams_count_ann,
                employees_count=employees_count_ann,
            )
        )

        search_term = (self.request.query_params.get("q") or "").strip()
        if search_term and self.action in ("list", "search", "my_departments"):
            qs = qs.filter(
                Q(name__icontains=search_term)
                | Q(description__icontains=search_term)
                | Q(director__first_name__icontains=search_term)
                | Q(director__last_name__icontains=search_term)
                | Q(director__email__icontains=search_term)
            )

        is_active = (self.request.query_params.get("is_active") or "").strip().lower()
        if is_active in ("1", "true", "yes", "y", "on"):
            qs = qs.filter(is_active=True)
        elif is_active in ("0", "false", "no", "n", "off"):
            qs = qs.filter(is_active=False)

        director_id = self.request.query_params.get("director_id")
        if director_id:
            qs = qs.filter(director_id=director_id)

        my_departments = (
            (self.request.query_params.get("my_departments") or "").strip().lower()
        )
        if my_departments in ("1", "true", "yes", "y", "on"):
            qs = qs.filter(director=self.request.user)

        # ⭐ PIN
        user = self.request.user
        if user.is_authenticated and user.role != UserRole.ADMIN:
            qs = qs.annotate(
                is_pinned=Case(
                    When(director=user, then=Value(1)),
                    When(teams__members=user, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ).order_by("-is_pinned", "-created_at", "id")
        else:
            qs = qs.order_by("-created_at", "id")

        return qs.distinct()

    def _apply_sql_ordering(self, queryset):
        ordering = (self.request.query_params.get("ordering") or "").strip()

        if ordering not in VALID_ORDERINGS:
            return queryset.order_by("-created_at", "id")

        if ordering in ("name", "-name"):
            desc = ordering.startswith("-")
            return queryset.annotate(_name_ci=Lower("name")).order_by(
                ("-" if desc else "") + "_name_ci", "id"
            )

        return queryset.order_by(ordering, "id")

    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)
        return self._apply_sql_ordering(qs)

    def perform_create(self, serializer):
        safe_cache_delete_pattern(DEPARTMENTS_CACHE_PATTERN)
        serializer.save()

    def perform_update(self, serializer):
        safe_cache_delete_pattern(DEPARTMENTS_CACHE_PATTERN)
        serializer.save()

    def perform_destroy(self, instance):
        safe_cache_delete_pattern(DEPARTMENTS_CACHE_PATTERN)
        if hasattr(instance, "teams") and instance.teams.exists():
            raise ValidationError(
                "Impossible de supprimer un département contenant des équipes."
            )
        instance.delete()

    @action(detail=False, methods=["get"], url_path="my-departments")
    def my_departments(self, request):
        queryset = self.filter_queryset(
            self.get_queryset().filter(director=request.user)
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response({"data": serializer.data, "total": queryset.count()})

    @action(detail=True, methods=["get"], url_path="teams")
    def teams(self, request, pk=None):
        department = self.get_object()

        if request.user.role != UserRole.ADMIN and not self._is_scoped_department(
            department
        ):
            raise PermissionDenied("Accès refusé.")

        qs = (
            Teams.objects.filter(department=department)
            .select_related("owner")
            .annotate(members_count=Count("members", distinct=True))
            .order_by("name")
        )
        return Response(TeamsLiteSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        search_term = (request.query_params.get("q") or "").strip()

        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except ValueError:
            page = 1

        try:
            limit = int(request.query_params.get("limit", 10))
        except ValueError:
            limit = 10
        limit = min(max(limit, 1), 100)

        queryset = self.filter_queryset(self.get_queryset())
        total = queryset.count()
        start = (page - 1) * limit
        rows = list(queryset[start : start + limit])

        serializer = self.get_serializer(rows, many=True)
        return Response(
            {
                "data": serializer.data,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit if total else 0,
                "query": search_term,
            }
        )

    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        try:
            now = datetime.now()
            qs = self.get_queryset()
            total_departments = qs.count()
            total_employees = qs.aggregate(total=Sum("employees_count"))["total"] or 0
            avg_per_department = (
                round(total_employees / total_departments) if total_departments else 0
            )
            this_month_count = qs.filter(
                created_at__year=now.year, created_at__month=now.month
            ).count()

            return Response(
                {
                    "total_departments": total_departments,
                    "total_employees": total_employees,
                    "avg_per_department": avg_per_department,
                    "this_month_count": this_month_count,
                    "timestamp": now.isoformat(),
                }
            )
        except Exception as e:
            logger.error("Erreur stats departments: %s", str(e), exc_info=True)
            return Response(
                {"error": "Erreur lors du calcul des statistiques"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
