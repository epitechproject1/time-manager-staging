from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ClockEventViewSet

router = DefaultRouter()
router.register(r"clock-events", ClockEventViewSet, basename="clock-events")

urlpatterns = [
    path("", include(router.urls)),
]
