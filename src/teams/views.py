import logging
from datetime import datetime

from django.core.cache import cache
from django.db.models import Count, Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Teams
from .serializers import TeamsSerializer

logger = logging.getLogger(__name__)
TEAMS_CACHE_PATTERN = "teams:*"


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
        tags=["Teams"],
        summary="Lister les équipes",
        description="Récupère la liste des équipes avec possibilité de recherche",
        parameters=[
            OpenApiParameter(
                name="q",
                description="Recherche (nom, description, département, propriétaire)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="department_id",
                description="Filtrer par département",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="owner_id",
                description="Filtrer par propriétaire",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="my_teams",
                description="Afficher uniquement mes équipes (true/false)",
                required=False,
                type=bool,
            ),
        ],
    ),
    retrieve=extend_schema(
        tags=["Teams"],
        summary="Détail d'une équipe",
        description="Récupère les détails complets d'une équipe spécifique",
    ),
    create=extend_schema(
        tags=["Teams"],
        summary="Créer une équipe",
        description="Crée une nouvelle équipe.",
    ),
    update=extend_schema(
        tags=["Teams"],
        summary="Mettre à jour une équipe",
        description="Met à jour complètement une équipe existante",
    ),
    partial_update=extend_schema(
        tags=["Teams"],
        summary="Mettre à jour partiellement une équipe",
        description="Met à jour partiellement les champs d'une équipe",
    ),
    destroy=extend_schema(
        tags=["Teams"],
        summary="Supprimer une équipe",
        description="Supprime définitivement une équipe",
    ),
)
class TeamsViewSet(ModelViewSet):
    serializer_class = TeamsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = (
            Teams.objects.all()
            .select_related("owner", "department")
            .prefetch_related("members")
            .annotate(members_count=Count("members", distinct=True))
            .order_by("-created_at")
        )

        search_term = (self.request.query_params.get("q") or "").strip()
        if search_term:
            qs = qs.filter(
                Q(name__icontains=search_term)
                | Q(description__icontains=search_term)
                | Q(department__name__icontains=search_term)
                | Q(owner__first_name__icontains=search_term)
                | Q(owner__last_name__icontains=search_term)
                | Q(owner__email__icontains=search_term)
            ).distinct()

        department_id = self.request.query_params.get("department_id")
        if department_id:
            qs = qs.filter(department_id=department_id)

        owner_id = self.request.query_params.get("owner_id")
        if owner_id:
            qs = qs.filter(owner_id=owner_id)

        my_teams_param = (
            (self.request.query_params.get("my_teams") or "").strip().lower()
        )
        if my_teams_param in ("1", "true", "yes", "y", "on"):
            qs = qs.filter(owner=self.request.user)

        return qs

    def list(self, request, *args, **kwargs):
        """Override pour ajouter des métadonnées dans la réponse"""
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
        safe_cache_delete_pattern(TEAMS_CACHE_PATTERN)

        owner = serializer.validated_data.get("owner", None)
        if owner is None:
            serializer.save(owner=self.request.user)
        else:
            serializer.save()

    def perform_update(self, serializer):
        safe_cache_delete_pattern(TEAMS_CACHE_PATTERN)
        serializer.save()

    def perform_destroy(self, instance):
        safe_cache_delete_pattern(TEAMS_CACHE_PATTERN)
        instance.delete()

    @extend_schema(
        tags=["Teams"],
        summary="Mes équipes",
        description="Récupère équipes dont le prop est l'utilisateur connecté",
    )
    @action(detail=False, methods=["get"], url_path="my-teams")
    def my_teams(self, request):
        teams = self.get_queryset().filter(owner=request.user)
        serializer = self.get_serializer(teams, many=True)
        return Response({"data": serializer.data, "total": teams.count()})

    @extend_schema(
        tags=["Teams"],
        summary="Rechercher des équipes",
        description="Recherche avancée d'équipes avec cache",
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
        """Endpoint de recherche dédié avec cache"""
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

        cache_key = f"teams:search:{search_term}:{page}:{limit}:{request.user.id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info("Cache hit pour: %s", cache_key)
            return Response(cached_result)

        queryset = self.get_queryset()
        if search_term:
            queryset = queryset.filter(
                Q(name__icontains=search_term)
                | Q(description__icontains=search_term)
                | Q(department__name__icontains=search_term)
                | Q(owner__first_name__icontains=search_term)
                | Q(owner__last_name__icontains=search_term)
                | Q(owner__email__icontains=search_term)
            ).distinct()

        total = queryset.count()
        start = (page - 1) * limit
        end = start + limit
        teams = queryset[start:end]

        serializer = self.get_serializer(teams, many=True)
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
        tags=["Teams"],
        summary="Statistiques des équipes",
        description="Récupère les statistiques agrégées (total, départements, ce mois)",
    )
    @action(detail=False, methods=["get"], url_path="stats")
    def stats(self, request):
        try:
            now = datetime.now()

            total_teams = Teams.objects.count()

            departments_count = (
                Teams.objects.filter(department__isnull=False)
                .values("department")
                .distinct()
                .count()
            )

            this_month_count = Teams.objects.filter(
                created_at__year=now.year, created_at__month=now.month
            ).count()

            user_teams_count = Teams.objects.filter(owner=request.user).count()

            teams_by_department = (
                Teams.objects.values("department__id", "department__name")
                .annotate(count=Count("id"))
                .order_by("-count")[:5]
            )

            return Response(
                {
                    "total_teams": total_teams,
                    "departments_count": departments_count,
                    "this_month_count": this_month_count,
                    "user_teams_count": user_teams_count,
                    "teams_by_department": list(teams_by_department),
                    "timestamp": now.isoformat(),
                }
            )

        except Exception as e:
            logger.error("Erreur stats: %s", str(e), exc_info=True)
            return Response(
                {"error": "Erreur lors du calcul des statistiques"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
