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
        description="Récupère la liste de toutes les équipes ",
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

    queryset = (
        Teams.objects.select_related("owner", "department")
        .all()
        .order_by("-created_at")
    )
    serializer_class = TeamsSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):

        if not serializer.validated_data.get('owner'):
            serializer.save(owner=self.request.user)
        else:
            serializer.save()

    def get_queryset(self):

        queryset = super().get_queryset()

        department_id = self.request.query_params.get('department')
        if department_id:
            queryset = queryset.filter(department_id=department_id)

        owner_id = self.request.query_params.get('owner')
        if owner_id:
            queryset = queryset.filter(owner_id=owner_id)

        if self.request.query_params.get('my_teams'):
            queryset = queryset.filter(owner=self.request.user)

        return queryset

    @extend_schema(
        tags=["Teams"],
        summary="Mes équipes",
        description="Récupère uniquement les équipes dont l'utilisateur co est pro",
    )
    @action(detail=False, methods=['get'], url_path='my-teams')
    def my_teams(self, request):

        teams = self.get_queryset().filter(owner=request.user)
        serializer = self.get_serializer(teams, many=True)
        return Response(serializer.data)
