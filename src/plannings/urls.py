from rest_framework.routers import DefaultRouter

from .views import PlanningViewSet

router = DefaultRouter()
router.register("plannings", PlanningViewSet, basename="planning")

urlpatterns = router.urls
