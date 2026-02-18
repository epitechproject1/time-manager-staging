import logging
from datetime import datetime

from django.core.cache import cache
from django.db.models import Count, Q, Sum
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from teams.models import Teams
from teams.serializers import TeamsLiteSerializer

from .models import Department
from .serializers import DepartmentSerializer

logger = logging.getLogger(__name__)
DEPARTMENTS_CACHE_PATTERN = "departments:*"


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


@extend_schema_view(
    list=extend_schema(
        tags=["Departments"],
        summary="Lister les départements",
        description="Récupère la liste des départements avec possibilité de recherche",
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
                description="Afficher uniquement les départements que je dirige ",
                required=False,
                type=bool,
            ),
        ],
    ),
    retrieve=extend_schema(tags=["Departments"], summary="Détail d’un département"),
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

    def get_queryset(self):
        qs = (
            Department.objects.all()
            .select_related("director")
            .annotate(
                teams_count=Count("teams", distinct=True),
                employees_count=Count("teams__members", distinct=True),
            )
            .order_by("-created_at")
        )

        search_term = (self.request.query_params.get("q") or "").strip()
        if search_term:
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

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
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

    @extend_schema(
        tags=["Departments"],
        summary="Lister les équipes d’un département",
        description="Retourne les équipes associées au département.",
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
        description="Recherche avancée de départements avec cache",
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
        ],
    )
    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        search_term = (request.query_params.get("q") or "").strip()

        try:
            page = int(request.query_params.get("page", 1))
        except ValueError:
            page = 1
        page = max(page, 1)

        try:
            limit = int(request.query_params.get("limit", 10))
        except ValueError:
            limit = 10
        limit = min(max(limit, 1), 100)

        cache_key = f"departments:search:{search_term}:{page}:{limit}:{request.user.id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info("Cache hit pour: %s", cache_key)
            return Response(cached_result)

        queryset = self.get_queryset()
        if search_term:
            queryset = queryset.filter(
                Q(name__icontains=search_term)
                | Q(description__icontains=search_term)
                | Q(director__first_name__icontains=search_term)
                | Q(director__last_name__icontains=search_term)
                | Q(director__email__icontains=search_term)
            ).distinct()

        total = queryset.count()
        start = (page - 1) * limit
        end = start + limit
        rows = queryset[start:end]

        serializer = self.get_serializer(rows, many=True)
        response_data = {
            "data": serializer.data,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if total else 0,
            "query": search_term,
        }

        cache.set(cache_key, response_data, 300)
        return Response(response_data)

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
