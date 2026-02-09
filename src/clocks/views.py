from rest_framework import viewsets, permissions
from .models import Clock
from .serializers import ClockSerializer

class ClockViewSet(viewsets.ModelViewSet):
    queryset = Clock.objects.all()
    serializer_class = ClockSerializer
    permission_classes = [permissions.IsAuthenticated]