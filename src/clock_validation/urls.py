from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ClockValidationViewSet

router = DefaultRouter()
router.register(
    r"clock-validations",
    ClockValidationViewSet,
    basename="clock-validations",
)

urlpatterns = [
    path("", include(router.urls)),
]
