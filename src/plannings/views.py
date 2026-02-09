from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from users.constants import UserRole
from .models import Planning
from .permissions import IsAdminOrOwner
from .serializers import PlanningSerializer


@extend_schema_view(
    list=extend_schema(summary="List plannings"),
    retrieve=extend_schema(summary="Retrieve a planning"),
    create=extend_schema(summary="Create a planning"),
    update=extend_schema(summary="Update a planning"),
    partial_update=extend_schema(summary="Partially update a planning"),
    destroy=extend_schema(summary="Delete a planning"),
)
class PlanningViewSet(ModelViewSet):
    queryset = Planning.objects.all()
    serializer_class = PlanningSerializer
    permission_classes = [IsAuthenticated, IsAdminOrOwner]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, "role", None) == UserRole.ADMIN:
            return Planning.objects.all()
        return Planning.objects.filter(user=user)
