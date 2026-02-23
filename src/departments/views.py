import logging
from datetime import datetime

from django.core.cache import cache
from django.db.models import Case, Count, IntegerField, Q, Sum, When
from django.db.models.functions import Lower
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from teams.models import Teams
from teams.serializers import TeamsLiteSerializer

from .models import Department
from .serializers import DepartmentSerializer

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
                name="q",
                description="Recherche (nom, description, directeur)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="is_active",
                description="Filtrer par statut (true/false)",
                required=False,
                type=bool,
            ),
            OpenApiParameter(
                name="director_id",
                description="Filtrer par directeur (id user)",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="my_departments",
                description="Afficher uniquement les départements que je dirige",
                required=False,
                type=bool,
            ),
            OpenApiParameter(
                name="ordering",
                description=(
                    "Récupère la liste des départements avec recherche, "
                    "filtres et tri"
                ),
                required=False,
                type=str,
            ),
        ],
    ),
    retrieve=extend_schema(tags=["Departments"], summary="Détail d'un département"),
    create=extend_schema(tags=["Departments"], summary="Créer un département"),
    update=extend_schema(tags=["Departments"], summary="Mettre à jour un département"),
    partial_update=extend_schema(
        tags=["Departments"], summary="Mettre à jour partiellement un département"
    ),
    destroy=extend_schema(tags=["Departments"], summary="Supprimer un département"),
)
class DepartmentViewSet(ModelViewSet):
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [OrderingFilter]
    ordering_fields = [
        "name",
        "created_at",
        "updated_at",
        "teams_count",
        "employees_count",
    ]
    ordering = ["-created_at"]

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
            ).distinct()

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

        return qs

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

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "data": serializer.data,
                "total": queryset.count(),
                "query": request.query_params.get("q", ""),
            }
        )

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

    @extend_schema(
        tags=["Departments"],
        summary="Lister les équipes d'un département",
        responses={200: TeamsLiteSerializer(many=True)},
    )
    @action(detail=True, methods=["get"], url_path="teams")
    def teams(self, request, pk=None):
        department = self.get_object()
        qs = (
            Teams.objects.filter(department=department)
            .select_related("owner")
            .annotate(members_count=Count("members", distinct=True))
            .order_by("name")
        )
        return Response(TeamsLiteSerializer(qs, many=True).data)

    @extend_schema(
        tags=["Departments"],
        summary="Rechercher des départements",
        parameters=[
            OpenApiParameter(
                name="q", description="Terme de recherche", required=True, type=str
            ),
            OpenApiParameter(
                name="page", description="Numéro de page", required=False, type=int
            ),
            OpenApiParameter(
                name="limit",
                description="Nombre de résultats par page (max 100)",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="ordering", description="Tri", required=False, type=str
            ),
        ],
    )
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

    @extend_schema(
        tags=["Departments"],
        summary="Statistiques des départements",
        description="Total Departments / Total Employees / Avg per Department",
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
                created_at__year=now.year,
                created_at__month=now.month,
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
