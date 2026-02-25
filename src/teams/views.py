import logging
from datetime import datetime

from django.core.cache import cache
from django.db.models import (
    Case,
    CharField,
    Count,
    Exists,
    IntegerField,
    OuterRef,
    Q,
    Value,
    When,
)
from django.db.models.functions import Concat, Lower
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from users.constants import UserRole

from .models import Teams
from .permissions import IsAdminOrReadOnlyTeamsDirectory
from .serializers import TeamsLiteSerializer, TeamsSerializer, UserMiniSerializer

logger = logging.getLogger(__name__)
TEAMS_CACHE_PATTERN = "teams:*"

VALID_ORDERINGS = {
    "name",
    "-name",
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
    "members_count",
    "-members_count",
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


@extend_schema_view(
    list=extend_schema(
        tags=["Teams"],
        summary="Lister les équipes",
        description="Annuaire des équipes (Lite) + filtres + tri",
        parameters=[
            OpenApiParameter(
                name="q", description="Recherche", required=False, type=str
            ),
            OpenApiParameter(
                name="department_id",
                description="Département",
                required=False,
                type=int,
            ),
            OpenApiParameter(
                name="owner_id", description="Owner", required=False, type=int
            ),
            OpenApiParameter(
                name="my_teams", description="Mes équipes", required=False, type=bool
            ),
            OpenApiParameter(
                name="ordering", description="Tri", required=False, type=str
            ),
        ],
    ),
    retrieve=extend_schema(tags=["Teams"], summary="Détail d'une équipe"),
    create=extend_schema(tags=["Teams"], summary="Créer une équipe"),
    update=extend_schema(tags=["Teams"], summary="Mettre à jour une équipe"),
    partial_update=extend_schema(tags=["Teams"], summary="Mise à jour partielle"),
    destroy=extend_schema(tags=["Teams"], summary="Supprimer une équipe"),
)
class TeamsViewSet(ModelViewSet):
    serializer_class = TeamsSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnlyTeamsDirectory]

    filter_backends = [OrderingFilter]
    ordering_fields = ["name", "created_at", "updated_at", "members_count"]
    ordering = ["-created_at"]

    def _is_scoped_team(self, team: Teams) -> bool:
        """
        Scoped si:
        - admin
        - owner
        - membre
        - director du département de la team
        """
        user = self.request.user
        if user.role == UserRole.ADMIN:
            return True
        if team.owner_id == user.id:
            return True
        if team.members.filter(id=user.id).exists():
            return True
        if (
            team.department_id
            and getattr(team.department, "director_id", None) == user.id
        ):
            return True
        return False

    def get_serializer_class(self):
        if self.action in ("list", "search", "my_teams"):
            return TeamsLiteSerializer

        if self.action == "retrieve":
            team = self.get_object()
            return (
                TeamsSerializer if self._is_scoped_team(team) else TeamsLiteSerializer
            )

        return TeamsSerializer

    def get_queryset(self):
        qs = (
            Teams.objects.all()
            .select_related("owner", "department", "department__director")
            .prefetch_related("members")
            .annotate(members_count=Count("members", distinct=True))
        )

        search_term = (self.request.query_params.get("q") or "").strip()
        if search_term and self.action in ("list", "search", "my_teams"):
            qs = qs.filter(
                Q(name__icontains=search_term)
                | Q(description__icontains=search_term)
                | Q(department__name__icontains=search_term)
                | Q(owner__first_name__icontains=search_term)
                | Q(owner__last_name__icontains=search_term)
                | Q(owner__email__icontains=search_term)
            )

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

        user = self.request.user
        if user.is_authenticated and user.role != UserRole.ADMIN:
            through = Teams.members.through

            is_member = Exists(
                through.objects.filter(teams_id=OuterRef("pk"), user_id=user.id)
            )

            qs = qs.annotate(
                _is_member=is_member,
                is_pinned=Case(
                    When(owner_id=user.id, then=Value(1)),
                    When(_is_member=True, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                ),
            ).order_by("-is_pinned", "-created_at", "id")
        else:
            qs = qs.order_by("-created_at", "id")

        return qs

    def filter_queryset(self, queryset):

        qs = super().filter_queryset(queryset)

        ordering = (self.request.query_params.get("ordering") or "").strip()
        if not ordering:
            return qs

        if ordering not in VALID_ORDERINGS:
            return qs

        if ordering in ("name", "-name"):
            desc = ordering.startswith("-")
            return qs.annotate(_name_ci=Lower("name")).order_by(
                ("-" if desc else "") + "_name_ci",
                "id",
            )

        return qs.order_by(ordering, "id")

    def list(self, request, *args, **kwargs):
        """
        Réponse uniforme pour le front: {data, total, query}
        même quand la pagination DRF est active.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            total = getattr(getattr(self, "paginator", None), "page", None)
            total = total.paginator.count if total else queryset.count()
            return Response(
                {
                    "data": serializer.data,
                    "total": total,
                    "query": request.query_params.get("q", ""),
                }
            )

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
        serializer.save()

    def perform_update(self, serializer):
        safe_cache_delete_pattern(TEAMS_CACHE_PATTERN)
        serializer.save()

    def perform_destroy(self, instance):
        safe_cache_delete_pattern(TEAMS_CACHE_PATTERN)
        instance.delete()

    @extend_schema(tags=["Teams"], summary="Lister/Rechercher les membres d'une équipe")
    @action(detail=True, methods=["get"], url_path="members")
    def members(self, request, pk=None):
        team = self.get_object()

        # if request.user.role != UserRole.ADMIN and not self._is_scoped_team(team):
        #     raise PermissionDenied("Accès refusé.")

        q = (request.query_params.get("q") or "").strip()
        ordering = (request.query_params.get("ordering") or "").strip()

        try:
            page = max(int(request.query_params.get("page", 1)), 1)
        except (ValueError, TypeError):
            page = 1

        try:
            page_size = int(request.query_params.get("page_size", 6))
        except (ValueError, TypeError):
            page_size = 6
        page_size = min(max(page_size, 1), 100)

        qs = team.members.all().annotate(
            full_name=Concat(
                "first_name",
                Value(" "),
                "last_name",
                output_field=CharField(),
            ),
            full_name_reversed=Concat(
                "last_name",
                Value(" "),
                "first_name",
                output_field=CharField(),
            ),
        )

        if q:
            qs = qs.filter(
                Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
                | Q(email__icontains=q)
                | Q(full_name__icontains=q)
                | Q(full_name_reversed__icontains=q)
            )

        allowed = {
            "first_name",
            "-first_name",
            "last_name",
            "-last_name",
            "email",
            "-email",
        }
        if ordering in allowed:
            qs = qs.order_by(ordering, "id")
        else:
            qs = qs.order_by("first_name", "last_name", "id")

        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        serializer = UserMiniSerializer(qs[start:end], many=True)
        return Response(
            {
                "count": total,
                "next": page * page_size < total,
                "previous": page > 1,
                "results": serializer.data,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size if total else 0,
            }
        )

    @action(detail=False, methods=["get"], url_path="my-teams")
    def my_teams(self, request):
        queryset = self.filter_queryset(self.get_queryset().filter(owner=request.user))
        serializer = TeamsLiteSerializer(queryset, many=True)
        return Response({"data": serializer.data, "total": queryset.count()})

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

        cache_key = f"teams:search:{search_term}:{page}:{limit}:{request.user.id}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return Response(cached_result)

        queryset = self.filter_queryset(self.get_queryset())
        total = queryset.count()

        start = (page - 1) * limit
        end = start + limit
        teams = queryset[start:end]

        serializer = TeamsLiteSerializer(teams, many=True)
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
