from django.db.models import Count
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import Teams
from .serializers import TeamsSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Teams"],
        summary="Lister les équipes",
        description="Récupère la liste de toutes les équipes",
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

        department_id = self.request.query_params.get("department_id")
        if department_id:
            qs = qs.filter(department_id=department_id)

        owner_id = self.request.query_params.get("owner_id")
        if owner_id:
            qs = qs.filter(owner_id=owner_id)

        my_teams = self.request.query_params.get("my_teams")
        if my_teams in ("1", "true", "True", "yes"):
            qs = qs.filter(owner=self.request.user)

        return qs

    def perform_create(self, serializer):

        if not serializer.validated_data.get("owner_id"):
            serializer.save(owner=self.request.user)
        else:
            serializer.save()

    @extend_schema(
        tags=["Teams"],
        summary="Mes équipes",
        description="Récupère les teams dont le prop est l'utilisateur connecté",
    )
    @action(detail=False, methods=["get"], url_path="my-teams")
    def my_teams(self, request):
        teams = self.get_queryset().filter(owner=request.user)
        serializer = self.get_serializer(teams, many=True)
        return Response(serializer.data)
