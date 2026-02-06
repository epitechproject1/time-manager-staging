from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from .models import Planning
from .serializers import PlanningSerializer


class PlanningViewSet(ModelViewSet):
    queryset = Planning.objects.all()
    serializer_class = PlanningSerializer
    permission_classes = [AllowAny]
