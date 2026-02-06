from rest_framework.routers import DefaultRouter

from .views import PlanningViewSet

router = DefaultRouter()
router.register("plannings", PlanningViewSet, basename="plannings")

urlpatterns = router.urls
